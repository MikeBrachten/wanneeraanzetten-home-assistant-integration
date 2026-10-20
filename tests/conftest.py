"""Run the custom integration inside Home Assistant's actual test runtime."""

from unittest.mock import patch

import pytest
from aiohttp.resolver import ThreadedResolver

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to discover the component in this repository."""


@pytest.fixture(autouse=True)
def isolated_test_dns():
    """Avoid resolver daemon threads across historical Home Assistant test harnesses."""
    with (
        patch("aiohttp.connector.DefaultResolver", ThreadedResolver),
        patch("homeassistant.helpers.aiohttp_client.AsyncResolver", ThreadedResolver, create=True),
    ):
        yield
