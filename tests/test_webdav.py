import pytest
from unittest.mock import patch, MagicMock
from pyfakefs.fake_filesystem_unittest import Patcher
from src.utils.webdav import WebDavManager

@pytest.fixture
def webdav_manager(fs):
    return WebDavManager()


def test_mount_webdav(webdav_manager, fs):
    fs.create_file('/path/to/mount_point', contents='Initial state before mount.')
    with patch("subprocess.run") as mock_subprocess_run:
        mock_subprocess_run.return_value = MagicMock()
        webdav_manager.mount_webdav()
        mock_subprocess_run.assert_called_once_with([
            'rclone',
            'mount',
            f"{webdav_manager.settings.remote_name}:",
            webdav_manager.settings.mount_point,
            webdav_manager.settings.rclone_settings,
            '--daemon'], check=True)


def test_unmount_webdav(webdav_manager, fs):
    fs.create_dir('/path/to/mount_point')
    with patch("subprocess.run") as mock_subprocess_run:
        mock_subprocess_run.return_value = MagicMock()
        webdav_manager.unmount_webdav()
        mock_subprocess_run.assert_called_once_with([
            'fusermount', '-u', webdav_manager.settings.mount_point], check=True)