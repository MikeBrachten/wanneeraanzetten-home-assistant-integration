"""Run the custom integration inside Home Assistant's actual test runtime."""

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to discover the component in this repository."""
