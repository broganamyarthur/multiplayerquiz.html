"""Shared test setup, loaded by pytest before the tests run."""
import os

from werkzeug.security import generate_password_hash

# Use a temporary in-memory database for tests, so they never touch real data.
os.environ["DATABASE_URL"] = "sqlite://"

# A known admin password for tests only. The real one is set as a secret in Azure.
TEST_ADMIN_PASSWORD = "test-password"
os.environ["ADMIN_PASSWORD_HASH"] = generate_password_hash(TEST_ADMIN_PASSWORD)