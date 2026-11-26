"""Shared test setup, loaded by pytest before the tests run."""
import os

# Use a temporary in-memory database for tests, so they never touch real data.
os.environ["DATABASE_URL"] = "sqlite://"