import subprocess
import os
from src.settings.manager import settings_manager
from loguru import logger


class WebDavManager:
    def __init__(self):
        self.settings = settings_manager.settings.webdav

    def mount_webdav(self):
        if not os.path.exists(self.settings.mount_point):
            os.makedirs(self.settings.mount_point)
        subprocess.run([
            'rclone',
            'mount',
            self.settings.remote_name + ':',
            self.settings.mount_point,
            self.settings.rclone_settings, 
            '--daemon'], check=True)

        logger.info(f"Mounted WebDAV remote {self.settings.mount_point} at {self.settings.mount_point}")

    def unmount_webdav(self):
        subprocess.run(['fusermount', '-u', self.settings.mount_point], check=True)
        logger.info(f"Unmounted WebDAV remote {self.settings.mount_point}")