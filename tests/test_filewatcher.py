import pytest
import os
from pyfakefs.fake_filesystem_unittest import Patcher
from unittest.mock import patch, MagicMock

from teemo.utils.filewatcher import FileWatcher


class TestFileWatcher:
    @pytest.fixture
    def mock_plex_updater(self):
        with patch('teemo.utils.filewatcher.PlexUpdater') as MockPlexUpdater:
            mock_plex_updater_instance = MockPlexUpdater.return_value
            # Mock the validate method to return True and set up a mock Plex server
            mock_plex_updater_instance.validate.return_value = True
            mock_plex_updater_instance.initialized = True
            mock_plex_server = MagicMock()
            mock_plex_updater_instance.plex = mock_plex_server
            mock_plex_server.library.sections.return_value = [
                MagicMock(title='movies', key='1', type='movie'),
                MagicMock(title='shows', key='2', type='show')
            ]
            yield MockPlexUpdater, mock_plex_updater_instance

    @pytest.fixture
    def file_watcher(self, mock_plex_updater):
        _, mock_plex_updater_instance = mock_plex_updater
        file_watcher = FileWatcher()
        file_watcher.plex_updater = mock_plex_updater_instance
        return file_watcher

    def test_toucher_movies(self, file_watcher, mock_plex_updater):
        _, mock_plex_updater_instance = mock_plex_updater

        with Patcher() as patcher:
            # Create necessary directories
            patcher.fs.create_dir(file_watcher.file_monitor_settings.rclone_path)
            patcher.fs.create_dir(file_watcher.file_monitor_settings.symlink_path)

            for lib in file_watcher.file_monitor_settings.library_paths:
                lib_path = os.path.join(file_watcher.file_monitor_settings.rclone_path, lib)
                patcher.fs.create_dir(lib_path)
                patcher.fs.create_file(os.path.join(lib_path, "test.mkv"))

            src = os.path.join(file_watcher.file_monitor_settings.rclone_path,
                               file_watcher.file_monitor_settings.library_paths[0], "test.mkv")
            file_watcher.mushroom_tosser(src)

            original_filename = "test.mkv"
            symlink_path = os.path.join(file_watcher.file_monitor_settings.symlink_path,
                                        file_watcher.file_monitor_settings.library_paths[0], original_filename)

            assert patcher.fs.exists(symlink_path)
            assert patcher.fs.islink(symlink_path)
            assert patcher.fs.readlink(symlink_path) == src

            # Verify that PlexUpdater's refresh_library method was called
            mock_plex_updater_instance.refresh_library.assert_called_with(
                file_watcher.file_monitor_settings.library_paths[0])

    def test_toucher_shows(self, file_watcher, mock_plex_updater):
        _, mock_plex_updater_instance = mock_plex_updater

        with Patcher() as patcher:
            # Create necessary directories
            patcher.fs.create_dir(file_watcher.file_monitor_settings.rclone_path)
            patcher.fs.create_dir(file_watcher.file_monitor_settings.symlink_path)

            for lib in file_watcher.file_monitor_settings.library_paths:
                lib_path = os.path.join(file_watcher.file_monitor_settings.rclone_path, lib)
                patcher.fs.create_dir(lib_path)
                patcher.fs.create_file(os.path.join(lib_path, "episode.mp4"))

            src = os.path.join(file_watcher.file_monitor_settings.rclone_path,
                               file_watcher.file_monitor_settings.library_paths[1], "episode.mp4")
            file_watcher.mushroom_tosser(src)

            original_filename = "episode.mp4"
            symlink_path = os.path.join(file_watcher.file_monitor_settings.symlink_path,
                                        file_watcher.file_monitor_settings.library_paths[1], original_filename)

            assert patcher.fs.exists(symlink_path)
            assert patcher.fs.islink(symlink_path)
            assert patcher.fs.readlink(symlink_path) == src

            # Verify that PlexUpdater's refresh_library method was called
            mock_plex_updater_instance.refresh_library.assert_called_with(
                file_watcher.file_monitor_settings.library_paths[1])

    def test_toucher_delete(self, file_watcher, mock_plex_updater):
        _, mock_plex_updater_instance = mock_plex_updater

        with Patcher() as patcher:
            # Create necessary directories
            patcher.fs.create_dir(file_watcher.file_monitor_settings.rclone_path)
            patcher.fs.create_dir(file_watcher.file_monitor_settings.symlink_path)

            for lib in file_watcher.file_monitor_settings.library_paths:
                lib_path = os.path.join(file_watcher.file_monitor_settings.rclone_path, lib)
                patcher.fs.create_dir(lib_path)
                patcher.fs.create_file(os.path.join(lib_path, "test.mkv"))

            src = os.path.join(file_watcher.file_monitor_settings.rclone_path,
                               file_watcher.file_monitor_settings.library_paths[0], "test.mkv")
            file_watcher.mushroom_tosser(src)

            original_filename = "test.mkv"
            symlink_path = os.path.join(file_watcher.file_monitor_settings.symlink_path,
                                        file_watcher.file_monitor_settings.library_paths[0], original_filename)
            assert patcher.fs.exists(symlink_path)
            assert patcher.fs.islink(symlink_path)
            assert patcher.fs.readlink(symlink_path) == src

            # Simulate file deletion
            patcher.fs.remove_object(src)
            file_watcher.mushroom_tosser(src, etype="delete")

            assert not patcher.fs.exists(symlink_path)

            # Verify that PlexUpdater's refresh_library method was called
            mock_plex_updater_instance.refresh_library.assert_called_with(
                file_watcher.file_monitor_settings.library_paths[0])