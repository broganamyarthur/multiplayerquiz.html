"""Automated accessibility checks (US-08) for every page in the app.

These cover what code can check reliably: a language, a title, a phone-friendly
viewport, and a label for every input. Colour contrast and keyboard use are
checked with Lighthouse and by hand.
"""
from html.parser import HTMLParser

import pytest

from app import app, games, Game

GAME_ID = "a11ytest"

PAGES = {
    "home": lambda c: c.get("/"),
    "single player quiz": lambda c: c.get("/quiz"),
    "single player result": lambda c: c.post("/submit", data={}),
    "admin": lambda c: c.get("/admin"),
    "lobby": lambda c: c.get(f"/lobby/{GAME_ID}"),
    "multiplayer quiz": lambda c: c.get(f"/multiplayer_quiz/{GAME_ID}"),
    "multiplayer results": lambda c: c.get(f"/multiplayer_result/{GAME_ID}"),
}


class PageChecker(HTMLParser):
    """Reads a page's HTML and records the parts these tests check."""

    def __init__(self):
        super().__init__()
        self.lang = None
        self.title = ""
        self.in_title = False
        self.has_viewport = False
        self.inputs = []          # (attributes, wrapped in a <label>?)
        self.label_targets = set()
        self.label_depth = 0
        self.has_main = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main" or a.get("role") == "main":
            self.has_main = True
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta" and a.get("name") == "viewport":
            self.has_viewport = True
        elif tag == "label":
            self.label_depth += 1
            if a.get("for"):
                self.label_targets.add(a["for"])
        elif tag in ("input", "textarea", "select") and a.get("type") != "hidden":
            self.inputs.append((a, self.label_depth > 0))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "label":
            self.label_depth = max(0, self.label_depth - 1)

    def handle_data(self, data):
        if self.in_title:
            self.title += data

    def unlabelled_inputs(self):
        return [
            a for a, wrapped in self.inputs
            if not (wrapped or a.get("aria-label") or a.get("id") in self.label_targets)
        ]


@pytest.fixture(autouse=True)
def game_to_view():
    """A game in progress, so the lobby, quiz and results pages have something to show."""
    with app.app_context():
        game = Game(GAME_ID)
    game.add_player("p1", "Alice")
    games[GAME_ID] = game
    yield
    games.pop(GAME_ID, None)


def check(page_name):
    response = PAGES[page_name](app.test_client())
    assert response.status_code == 200
    checker = PageChecker()
    checker.feed(response.get_data(as_text=True))
    return checker


@pytest.mark.parametrize("page_name", PAGES)
def test_page_says_it_is_in_english(page_name):
    assert check(page_name).lang == "en"


@pytest.mark.parametrize("page_name", PAGES)
def test_page_has_a_title(page_name):
    assert check(page_name).title.strip() != ""


@pytest.mark.parametrize("page_name", PAGES)
def test_page_fits_phone_screens(page_name):
    assert check(page_name).has_viewport


@pytest.mark.parametrize("page_name", PAGES)
def test_every_input_has_a_label(page_name):
    assert check(page_name).unlabelled_inputs() == []


@pytest.mark.parametrize("page_name", PAGES)
def test_page_marks_its_main_content(page_name):
    assert check(page_name).has_main
