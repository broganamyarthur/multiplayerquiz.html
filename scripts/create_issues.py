"""Create the Quiz Web App user stories as GitHub issues and add them to a project board.

Usage (from the repo folder, after `gh auth login` and `gh auth refresh -s project`):
    python create_issues.py --dry-run      # print what would be created
    python create_issues.py                # create labels and issues

Requires the GitHub CLI (gh). Re-running creates duplicate issues, so run it once.
"""

import argparse
import subprocess

REPO = "broganamyarthur/multiplayerquiz.html"
PROJECT = "quiz web app"  # must match the GitHub Projects board title exactly

LABELS = {
    "user-story": ("1d76db", "User story from the requirements doc"),
    "must-have": ("b60205", "MoSCoW: must have (Pass)"),
    "should-have": ("fbca04", "MoSCoW: should have (Distinction)"),
}

# (id, title, priority, estimate_days, story, acceptance criteria, links)
STORIES = [
    ("US-01", "Host a live quiz", "must-have", 0.25,
     "As a quiz host, I want to start a game and get a short join code, so that the team can join from the all-hands call.",
     ["Given I am on the home page, when I choose to host a quiz, then a game is created with a unique join code.",
      "Given a game exists, when players join, then I see each name appear in the lobby.",
      "Given players are in the lobby, when I press Start, then no new players can join."],
     "NFR-01"),
    ("US-02", "Join with a code", "must-have", 0.25,
     "As a participant, I want to join with a code and a display name, so that I can play without creating an account.",
     ["Given a valid code, when I enter it with my name, then I enter the lobby and others see me.",
      "Given a wrong or expired code, when I try to join, then I see a clear error and can try again.",
      "Given a game has started, when I try to join, then I am told it is already in progress."],
     "NFR-05, NFR-08"),
    ("US-03", "Everyone sees the same question", "must-have", 0.5,
     "As a quiz host, I want to move everyone to the next question together, so that the quiz runs at the pace of the meeting.",
     ["Given a game has started, when I press Next, then every player sees the same new question within 1 second.",
      "Given a question is showing, when a player answers, then the host sees how many players have answered.",
      "Given the last question is answered, when I press Finish, then every player goes to the results screen."],
     "NFR-01, NFR-02"),
    ("US-04", "Live leaderboard and results", "must-have", 0.25,
     "As a participant, I want to see the leaderboard after each question and at the end, so that I know where I rank.",
     ["Given a question closes, when scores update, then the leaderboard shows every player sorted by score.",
      "Given the game finishes, when results show, then the winner is highlighted and ties are shown as ties."],
     "NFR-01"),
    ("US-05", "Manage the question bank", "must-have", 1.5,
     "As a quiz host, I want to add, edit and delete questions, so that each Friday's quiz is fresh and suits the team.",
     ["Given I am signed in as an admin, when I add a question with options and one correct answer, then it is saved to the database and appears in the list.",
      "Given a question exists, when I edit or delete it, then the change is saved and shown straight away.",
      "Given I search by keyword or category, when results load, then only matching questions show.",
      "Given a question has no correct answer, or fewer than 2 options, when I save, then I see a validation error."],
     "NFR-04. Full CRUD REST API backed by PostgreSQL. Built test first (TDD)."),
    ("US-06", "Admin sign-in", "must-have", 0.5,
     "As a quiz host, I want the question bank to be protected, so that only admins can change questions.",
     ["Given I am not signed in, when I open the admin page or call an admin API, then I am redirected or refused (401/403).",
      "Given valid admin credentials, when I sign in, then I can manage questions until I sign out or the session expires.",
      "Given 5 failed sign-ins in a row, when I try again, then I am slowed down or locked out for a short time."],
     "NFR-03, NFR-04"),
    ("US-07", "Fair scoring", "must-have", 0.5,
     "As a participant, I want scoring to be checked by the server, so that nobody can cheat.",
     ["Given I have answered a question, when I submit again, then my first answer stands and my score does not change.",
      "Given a message with an invalid question number, player or answer, when the server receives it, then it is rejected and logged without crashing the game.",
      "Given the question has closed, when a late answer arrives, then it is not scored."],
     "NFR-03. Fixes the existing repeat-answer defect."),
    ("US-08", "Usable by everyone, on any device", "must-have", 0.5,
     "As a participant, I want the quiz to work with a keyboard, a screen reader and a phone, so that everyone in the team can take part.",
     ["Given I only use a keyboard, when I play a full game, then I can reach and pick every answer.",
      "Given a screen reader, when a question appears, then the question and options are read out.",
      "Given a phone screen 360 px wide, when I play, then nothing is cut off and buttons are easy to tap."],
     "NFR-05"),
    ("US-09", "Quiz survives a server failure", "must-have", 1,
     "As the platform owner, I want games to carry on if one replica stops, so that a failure does not ruin the Friday quiz.",
     ["Given 2 replicas and a live game, when one replica is stopped, then players reconnect and the game continues with scores intact.",
      "Given game state, when any replica handles a request, then it reads the same state from Redis."],
     "NFR-02. Game state and Socket.IO messages move from in-memory dictionaries to Redis."),
    ("US-10", "Automated release to Azure", "must-have", 2,
     "As the platform owner, I want every merge to main to be tested, built and released through staging, so that releases are quick, safe and repeatable.",
     ["Given a pull request, when it is opened, then tests and security scans run, and it cannot merge unless they pass.",
      "Given a merge to main, when the pipeline runs, then a versioned image is pushed to Azure Container Registry and deployed to staging.",
      "Given staging passes its smoke test, when the release is approved, then it deploys to production with no downtime.",
      "Given a bad release, when I roll back, then the previous revision serves traffic again in under 5 minutes.",
      "Given an empty subscription, when I run the Bicep deployment, then all infrastructure is created from scratch."],
     "NFR-03, NFR-06"),
    ("US-11", "Monitoring and alerts", "must-have", 1.5,
     "As the platform owner, I want dashboards and alerts on the app's health, so that I know about problems before the team does.",
     ["Given the app is running, when I open the dashboard, then I see CPU, memory, request rate, error rate and health check status.",
      "Given the error rate goes above [5%] for 5 minutes, or the health check fails, then an alert fires and reaches me.",
      "Given an alert fires, when I open the runbook, then it tells me how to diagnose and fix the likely causes."],
     "NFR-09. Alert rules checked in CI with promtool."),
    ("US-12", "Backup and recovery", "must-have", 0.25,
     "As the platform owner, I want the question bank and results backed up, so that a mistake or failure does not lose them.",
     ["Given the database, when a day passes, then an automatic backup exists.",
      "Given a backup, when I follow the restore runbook, then the data is restored within 1 hour."],
     "NFR-06"),
    ("US-13", "Question timer behind a feature flag", "should-have", 0.5,
     "As a quiz host, I want an optional countdown on each question, so that the quiz keeps moving in a 1-hour meeting.",
     ["Given the FEATURE_QUESTION_TIMER flag is off, when a game runs, then it behaves exactly as before.",
      "Given the flag is on and I set 20 seconds, when a question shows, then every player sees the same countdown and answers close at zero.",
      "Given the flag is turned off in production, when the next game starts, then the timer is gone with no redeploy of code."],
     "NFR-01. Feature toggling (S20)."),
    ("US-14", "Season leaderboard", "should-have", 0.5,
     "As the team lead, I want scores saved across weeks, so that there is a running league that keeps people coming back.",
     ["Given a game finishes, when results are saved, then each player's score is added to the current season.",
      "Given I open the season page, when it loads, then players are ranked by total points with games played shown.",
      "Given a new quarter starts, when an admin starts a new season, then the table resets and the old season is kept."],
     "NFR-08"),
    ("US-15", "Engagement metrics", "should-have", 0.5,
     "As the team lead, I want to see how many people play each week, so that I can show the app is used and worth keeping.",
     ["Given games are played, when I open the dashboard, then I see games per week, players per game and answers per question.",
      "Given turnout drops by [30%] against the 4-week average, when the weekly check runs, then a low-priority alert or note is raised."],
     "NFR-09. Custom Prometheus metrics."),
    ("US-16", "Automatic weekly refresh and patching", "should-have", 0.5,
     "As the platform owner, I want the app rebuilt on the latest patched base image every week, so that security fixes land without manual work.",
     ["Given a weekly schedule, when it fires, then the pipeline rebuilds the image on the latest Python base image, scans it and releases a new revision through staging.",
      "Given the scan finds a high or critical vulnerability, when the rebuild runs, then the release stops and I am alerted.",
      "Given a dependency update is available, when Dependabot opens a pull request, then the normal pipeline tests it."],
     "NFR-03, NFR-06"),
]


def gh(args, dry_run):
    """Run a gh command, or just print it in dry-run mode."""
    if dry_run:
        print("gh", " ".join(args[:4]), "...")
        return
    subprocess.run(["gh", *args], check=True)


def issue_body(story, criteria, links, estimate):
    checklist = "\n".join(f"- [ ] {c}" for c in criteria)
    return (
        f"## Story\n{story}\n\n"
        f"## Acceptance criteria\n{checklist}\n\n"
        f"## Links\n{links}\n\n"
        f"**Estimate:** {estimate} days"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print commands without running them")
    args = parser.parse_args()

    for name, (colour, description) in LABELS.items():
        gh(["label", "create", name, "--repo", REPO, "--color", colour,
            "--description", description, "--force"], args.dry_run)

    for story_id, title, priority, estimate, story, criteria, links in STORIES:
        gh(["issue", "create", "--repo", REPO,
            "--title", f"{story_id}: {title}",
            "--body", issue_body(story, criteria, links, estimate),
            "--label", "user-story", "--label", priority,
            "--project", PROJECT], args.dry_run)
        print(f"Created {story_id}: {title}")


if __name__ == "__main__":
    main()
