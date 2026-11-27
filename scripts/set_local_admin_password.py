"""Save a hashed admin password to .env for running the app locally with Docker Compose.

Usage (from the project folder):
    python scripts/set_local_admin_password.py
    docker compose up -d

The password itself is never stored, only its hash. .env is in .gitignore,
so it is never committed. Production uses a separate secret in Azure.
"""
import getpass

from werkzeug.security import generate_password_hash

password = getpass.getpass("Choose an admin password: ")
confirm = getpass.getpass("Type it again: ")

if not password:
    raise SystemExit("The password can't be empty. Nothing was changed.")
if password != confirm:
    raise SystemExit("The passwords didn't match. Nothing was changed.")

with open(".env", "w", encoding="utf-8") as env_file:
    env_file.write(f"ADMIN_PASSWORD_HASH='{generate_password_hash(password)}'\n")

print("Saved the hashed password to .env. Restart the app with: docker compose up -d")
