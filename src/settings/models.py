"""Teemo settings models"""
import os
from typing import Callable, List

from pydantic import BaseModel, Field


class Observable(BaseModel):
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


class FileMonitorSettings(Observable):
    library_paths: List[str] = ["__all__"]
    touch_delay: int = 10
    writable_dir: str = "/tmp"
    dummy_file: str = "teemo.mushroom"
    ignored_files: List[str] = ["teemo.mushroom"]
    file_types: List[str] = ["*.mkv", "*.mp4", "*.avi", "*.m4v", "*.mov", "*.ts", "*.vob", "*.webm"]


class WebDavSettings(Observable):
    mount_point: str = "/mnt/debrid/"
    remote_name: str = "teemo"
    user_id: str = Field(default_factory=lambda: os.getenv('USER_ID', '1001'))
    rclone_settings: str = Field(default_factory=lambda: (
        f"--allow-other "
        f"--allow-non-empty "
        f"--bind=0.0.0.0 "
        f"--cache-dir=/cache "
        f"--config=/config/rclone/rclone.conf "
        f"--buffer-size=32M "
        f"--dir-cache-time=5s "
        f"--uid={os.getenv('USER_ID', 'default_user_id')} "
        f"--gid={os.getenv('USER_ID', 'default_user_id')} "
        f"--timeout=10m "
        f"--umask=002 "
        f"--use-mmap "
        f"--vfs-cache-min-free-space=off "
        f"--vfs-cache-max-age=1024h "
        f"--vfs-cache-max-size=150G "
        f"--vfs-cache-mode=full "
        f"--vfs-read-chunk-size-limit=64M "
        f"--vfs-read-chunk-size=1M "
        f"--async-read=true "
        f"--bwlimit=512M "
        f"--rc "
        f"--rc-addr=0.0.0.0:19998 "
        f"--rc-enable-metrics "
        f"--rc-no-auth "
        f"--rc-web-gui "
        f"--rc-web-gui-no-open-browser "
        f"--no-check-certificate "
        f"--no-traverse "
        f"--ignore-existing "
        f"-v"
    ))


class TeemoModel(Observable):
    debug: bool = False
    file_monitor: FileMonitorSettings = FileMonitorSettings()
    webdav: WebDavSettings = WebDavSettings()