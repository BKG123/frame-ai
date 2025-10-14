"""
Pytest configuration and fixtures for Frame AI evaluations.
"""

import pytest
import asyncio

from evals.config import IMAGES_DIR


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def fixtures_dir():
    """Fixture providing path to fixtures directory."""
    from evals.config import FIXTURES_DIR

    return FIXTURES_DIR


@pytest.fixture
def images_dir():
    """Fixture providing path to test images directory."""
    return IMAGES_DIR
