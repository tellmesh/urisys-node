"""Pytest configuration for urisys-node tests."""

import os


def pytest_configure(config):
    """Set environment variables for tests."""
    # Disable local wheelhouse to ensure tests use GitHub/PyPI sources
    # This prevents tests from picking up locally built wheels
    os.environ["URISYS_WHEELHOUSE"] = "/tmp/nonexistent-wheels"
