import watchdog.events
import watchdog.observers
from watchdog.observers.polling import PollingObserver
import time
import os

from src.settings.manager import settings_manager
from src.settings.models import WebDavSettings
from loguru import logger

PRODUCT_NAME = "teemo"


class FileWatcher:
    web_dav_settings: WebDavSettings
    debrid_folder: str

    def __init__(self):
        self.file_monitor_settings = settings_manager.settings.file_monitor
        self.web_dav_settings = settings_manager.settings.webdav
        self.debrid_folder = self.web_dav_settings.mount_point
        self.lasttouch = [time.time() - self.file_monitor_settings.touch_delay, ""]

    def toucher(self, src, dest="", etype=""):
        dummy_file_path = os.path.join(self.file_monitor_settings.writable_dir, self.file_monitor_settings.dummy_file)
        logger.debug(f"Dummy file path: {dummy_file_path}")
        for lib in self.file_monitor_settings.library_paths:
            lib_path = os.path.join(self.debrid_folder, lib)
            logger.debug(f"Checking library path: {lib_path}")
            logger.debug(f"src: {src}, dest: {dest}, etype: {etype}")
            if (
                    (etype == "move" and os.path.dirname(dest).startswith(lib_path) and self.lasttouch[0] + self.file_monitor_settings.touch_delay <= time.time())
                    or (etype == "move" and os.path.dirname(dest).startswith(lib_path) and self.lasttouch[1] != lib)
                    or (os.path.dirname(src).startswith(lib_path) and self.lasttouch[0] + self.file_monitor_settings.touch_delay <= time.time())
                    or (os.path.dirname(src).startswith(lib_path) and self.lasttouch[1] != lib)
            ):
                logger.debug(f"Condition met for touching")
                with open(dummy_file_path, "w"):
                    pass
                symlink_path = os.path.join(lib_path, self.file_monitor_settings.dummy_file)
                logger.debug(f"Symlink path: {symlink_path}")
                if os.path.islink(symlink_path):
                    logger.debug(f"Removing symlink: {symlink_path}")
                    os.remove(symlink_path)
                os.symlink(dummy_file_path, symlink_path)
                logger.info(f"Touched {lib_path}")
                self.lasttouch = [time.time(), lib]
                return
            elif (
                    self.lasttouch[0] + self.file_monitor_settings.touch_delay > time.time()
                    and os.path.dirname(src).startswith(lib_path)
                    or (etype == "move" and self.lasttouch[0] + self.file_monitor_settings.touch_delay > time.time() and os.path.dirname(dest).startswith(lib_path))
            ):
                logger.info(f"Nothing touched, touched {lib} under {self.file_monitor_settings.touch_delay} seconds ago")
                return
        logger.info("Nothing touched")

    class Handler(watchdog.events.PatternMatchingEventHandler):
        def __init__(self, monitor):
            super().__init__(patterns=monitor.file_monitor_settings.file_types, ignore_patterns=monitor.file_monitor_settings.ignored_files, ignore_directories=False, case_sensitive=False)
            self.monitor = monitor

        def on_created(self, event):
            try:
                logger.info(f"File created: {event.src_path}")
                self.monitor.toucher(event.src_path)
            except Exception as e:
                logger.error(f"Error in on_created: {e}")

        def on_deleted(self, event):
            try:
                logger.info(f"File deleted: {event.src_path}")
                self.monitor.toucher(event.src_path)
            except Exception as e:
                logger.error(f"Error in on_deleted: {e}")

        def on_moved(self, event):
            try:
                logger.info(f"File moved: {event.src_path} to {event.dest_path}")
                self.monitor.toucher(event.src_path, event.dest_path, "move")
            except Exception as e:
                logger.error(f"Error in on_moved: {e}")

    def start_monitoring(self):
        event_handler = self.Handler(self)
        observer = PollingObserver()
        observer.schedule(event_handler, path=self.web_dav_settings.mount_point, recursive=True)
        observer.start()
        return observer

    def stop_monitoring(self, observer):
        observer.stop()
        observer.join()
        logger.info("Stopped monitoring")