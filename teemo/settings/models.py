"""Teemo settings models"""

from typing import Callable, List, Any
from settings.migratable import MigratableBaseModel
from utils import version_file_path


class Observable(MigratableBaseModel):
    class Config:
        arbitrary_types_allowed = True

    _notify_observers: Callable = None

    @classmethod
    def set_notify_observers(cls, notify_observers_callable):
        cls._notify_observers = notify_observers_callable

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if self.__class__._notify_observers:
            with self._notify_observers_context():
                self.__class__._notify_observers()


def get_version() -> str:
    with open(version_file_path.resolve()) as file:
        return file.read() or "x.x.x"


class PlexLibraryModel(Observable):
    enabled: bool = True
    token: str = ""
    url: str = "http://localhost:32400"


class FileMonitorSettings(Observable):
    library_paths: List[str] = ["movies", "shows"]
    poll_interval_seconds: int = 5
    rclone_path: str = "/mnt/rclone"
    symlink_path: str = "/mnt/teemo-symlinks"
    ignored_files: List[str] = []
    file_types: List[str] = ["*.mkv", "*.mp4", "*.avi", "*.m4v", "*.mov", "*.ts", "*.vob", "*.webm"]

class TeemoModel(Observable):
    version: str = get_version()
    debug: bool = False
    file_monitor: FileMonitorSettings = FileMonitorSettings()
    plex: PlexLibraryModel = PlexLibraryModel()

    def __init__(self, **data: Any):
        current_version = get_version()
        existing_version = data.get('version', current_version)
        super().__init__(**data)
        if existing_version < current_version:
            self.version = current_version