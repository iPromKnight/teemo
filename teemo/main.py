import time

from utils.logger import logger
from utils.filewatcher import FileWatcher
from settings.manager import settings_manager


def main():
    if not settings_manager.settings_file.exists():
        logger.log("INFO", "Settings file not found, creating default settings")
        settings_manager.save()
    logger.info(
        f"Teemo - in a bush - watching "
        f"{settings_manager.settings.file_monitor.rclone_path} "
        f"and getting ready to stack mushrooms on "
        f"{','.join(settings_manager.settings.file_monitor.library_paths)}")
    file_watcher = FileWatcher()
    observer = file_watcher.start_monitoring()
    try:
        while True:
            time.sleep(1)
            file_watcher.process_changes()
    except KeyboardInterrupt:
        logger.info("Teemo Exiting...")
    finally:
        file_watcher.stop_monitoring(observer)
        logger.info("Teemo Exited")


if __name__ == "__main__":
    main()