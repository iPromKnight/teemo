import pytest
import os
from unittest.mock import patch, MagicMock, ANY

from pyfakefs.fake_filesystem_unittest import Patcher

from src.utils.filewatcher import FileWatcher
from src.utils.logger import logger


@pytest.fixture
def file_watcher():
    return FileWatcher()


def test_toucher(file_watcher):
    dummy_file_path = os.path.join(file_watcher.file_monitor_settings.writable_dir, file_watcher.file_monitor_settings.dummy_file)

    with Patcher() as patcher:
        patcher.fs.create_dir(file_watcher.debrid_folder)
        for lib in file_watcher.file_monitor_settings.library_paths:
            lib_path = os.path.join(file_watcher.debrid_folder, lib)
            patcher.fs.create_dir(lib_path)
            patcher.fs.create_file(os.path.join(lib_path, "test.mkv"))

        if not patcher.fs.exists(file_watcher.file_monitor_settings.writable_dir):
            patcher.fs.create_dir(file_watcher.file_monitor_settings.writable_dir)

        src = os.path.join(file_watcher.debrid_folder, file_watcher.file_monitor_settings.library_paths[0], "test.mkv")
        file_watcher.toucher(src)

        symlink_path = os.path.join(file_watcher.debrid_folder, file_watcher.file_monitor_settings.library_paths[0], file_watcher.file_monitor_settings.dummy_file)

        logger.debug(f"Checking if {dummy_file_path} exists: {patcher.fs.exists(dummy_file_path)}")
        logger.debug(f"Checking if {symlink_path} is a symlink: {patcher.fs.islink(symlink_path)}")

        assert patcher.fs.exists(dummy_file_path)
        assert patcher.fs.islink(symlink_path)