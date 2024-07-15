import time
from loguru import logger
from utils.logger import setup_logger
from utils.webdav import WebDavManager
from utils.filewatcher import FileWatcher
from settings.manager import settings_manager

web_dav_manager = WebDavManager()
file_watcher = FileWatcher()

setup_logger("DEBUG")
web_dav_manager.mount_webdav()
observer = file_watcher.start_monitoring()
settings = settings_manager.settings
try:
    logger.info(f"Teemo - in a bush - watching {settings.webdav.debrid_folder} and getting ready to stack mushrooms on {', '.join(settings.file_monitor_settings.library_paths)}")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Teemo Exiting...")
finally:
    file_watcher.stop_monitoring(observer)
    web_dav_manager.unmount_webdav()
    logger.info("Teemo Exited")