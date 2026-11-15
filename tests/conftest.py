import pytest
from shared.config import settings

@pytest.fixture(autouse=True, scope="session")
def configure_test_settings():
    settings.TTS_PROVIDER = "mock"
