import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
from src.settings.manager import SettingsManager
from src.settings.models import TeemoModel

@pytest.fixture
def settings_manager():
    return SettingsManager()

def test_load_settings(settings_manager):
    settings_json = json.dumps(TeemoModel().model_dump())
    with patch("builtins.open", mock_open(read_data=settings_json)) as mock_file:
        settings_manager.load()
        mock_file.assert_called_once_with(settings_manager.settings_file, "r", encoding="utf-8")
        assert isinstance(settings_manager.settings, TeemoModel)

def test_save_settings(settings_manager):
    with patch("builtins.open", mock_open()) as mock_file:
        settings_manager.save()
        mock_file.assert_called_once_with(settings_manager.settings_file, "w", encoding="utf-8")

def test_notify_observers(settings_manager):
    mock_observer = MagicMock()
    settings_manager.register_observer(mock_observer)
    settings_manager.notify_observers()
    mock_observer.assert_called_once()