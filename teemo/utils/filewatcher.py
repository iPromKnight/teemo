import watchdog.events
import watchdog.observers
from watchdog.observers.polling import PollingObserver
import os
import time
import threading
from collections import defaultdict
from loguru import logger
from libraries.plex import PlexUpdater
from settings.manager import settings_manager


class FileWatcher:
    def __init__(self):
        self.file_monitor_settings = settings_manager.settings.file_monitor
        self.plex = PlexUpdater()
        self.changes = defaultdict(list)
        self.last_processed = time.time()
        self.lock = threading.Lock()
        self.check_symlinks()
        self.processing_thread = threading.Thread(target=self.process_changes)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def record_change(self, etype, src, dest=""):
        with self.lock:
            self.changes[etype].append((src, dest))
        logger.debug(f"Recorded change: {etype} - {src} -> {dest}")

    def process_changes(self):
        while True:
            time.sleep(self.file_monitor_settings.poll_interval_seconds)

            with self.lock:
                changes_copy = dict(self.changes)
                self.changes.clear()

            for etype, changes in changes_copy.items():
                for src, dest in changes:
                    self.mushroom_tosser(src, dest, etype)

    def update_plex(self, lib):
        if self.plex.initialized:
            self.plex.refresh_library(lib)

    def check_symlinks(self):
        """Check and remove invalid symlinks at startup and create missing ones."""
        logger.info("Checking symlinks at startup")
        allowed_extensions = tuple(ext.lstrip('*') for ext in self.file_monitor_settings.file_types)
        libsToUpdate = []  # Correctly instantiate the list
        for lib in self.file_monitor_settings.library_paths:
            symlink_dir = os.path.join(self.file_monitor_settings.symlink_path, lib)
            rclone_dir = os.path.join(self.file_monitor_settings.rclone_path, lib)
            if os.path.exists(symlink_dir):
                for root, _, files in os.walk(symlink_dir):
                    for file in files:
                        symlink_path = os.path.join(root, file)
                        if os.path.islink(symlink_path) and not os.path.exists(os.readlink(symlink_path)):
                            self.remove_symlink(symlink_path)
                            if lib not in libsToUpdate:
                                libsToUpdate.append(lib)

            if os.path.exists(rclone_dir):
                for root, _, files in os.walk(rclone_dir):
                    for file in files:
                        if not file.endswith(allowed_extensions):
                            continue

                        src_path = os.path.join(root, file)

                        symlink_path = os.path.join(self.file_monitor_settings.symlink_path, lib, file)
                        if not os.path.exists(symlink_path):
                            self.create_symlink(src_path, symlink_path)
                            if lib not in libsToUpdate:
                                libsToUpdate.append(lib)
        if libsToUpdate:
            for lib in libsToUpdate:
                self.update_plex(lib)

    def mushroom_tosser(self, src, dest="", etype=""):
        for lib in self.file_monitor_settings.library_paths:
            lib_path = os.path.join(self.file_monitor_settings.rclone_path, lib)
            logger.debug(f"Checking library path: {lib_path}")
            original_filename = os.path.basename(src)
            symlink_path = os.path.join(self.file_monitor_settings.symlink_path, lib, original_filename)

            if etype == "delete":
                logger.debug(f"Handling delete for {src}")
                if os.path.islink(symlink_path) or os.path.exists(symlink_path):
                    self.remove_symlink(symlink_path)
                    logger.info(f"Removed symlink {symlink_path} for deleted file {src}")
                    self.update_plex(lib)
                return

            logger.debug(f"Handling etype: {etype}, src: {src}, dest: {dest}")

            if (
                    (etype == "move" and os.path.dirname(dest).startswith(lib_path))
                    or os.path.dirname(src).startswith(lib_path)
            ):
                self.create_symlink(src, symlink_path)
                logger.info(f"Mushroom Thrown: {lib_path} and created symlink {symlink_path}")
                self.update_plex(lib)
                return
        logger.info("No Mushrooms to throw.")

    @staticmethod
    def create_symlink(src, symlink_path):
        """Create a symlink for the given source file, resolving absolute paths."""
        abs_src = os.path.abspath(src)
        abs_symlink_path = os.path.abspath(symlink_path)

        if not os.path.exists(os.path.dirname(abs_symlink_path)):
            os.makedirs(os.path.dirname(abs_symlink_path))
        if os.path.islink(abs_symlink_path) or os.path.exists(abs_symlink_path):
            os.remove(abs_symlink_path)
        os.symlink(abs_src, abs_symlink_path)
        logger.info(f"Created symlink {abs_symlink_path} for file {abs_src}")

    @staticmethod
    def remove_symlink(symlink_path):
        """Remove the given symlink."""
        if os.path.islink(symlink_path) or os.path.exists(symlink_path):
            os.remove(symlink_path)
            logger.info(f"Removed invalid symlink: {symlink_path}")

    class Handler(watchdog.events.PatternMatchingEventHandler):
        def __init__(self, monitor):
            super().__init__(patterns=monitor.file_monitor_settings.file_types,
                             ignore_patterns=monitor.file_monitor_settings.ignored_files, ignore_directories=False,
                             case_sensitive=False)
            self.monitor = monitor

        def on_created(self, event):
            try:
                logger.info(f"File created: {event.src_path}")
                self.monitor.record_change("created", event.src_path)
            except Exception as e:
                logger.error(f"Error in on_created: {e}")

        def on_deleted(self, event):
            try:
                logger.info(f"File deleted: {event.src_path}")
                self.monitor.record_change("delete", event.src_path)
            except Exception as e:
                logger.error(f"Error in on_deleted: {e}")

        def on_moved(self, event):
            try:
                logger.info(f"File moved: {event.src_path} to {event.dest_path}")
                self.monitor.record_change("move", event.src_path, event.dest_path)
            except Exception as e:
                logger.error(f"Error in on_moved: {e}")

    def start_monitoring(self):
        event_handler = self.Handler(self)
        observer = PollingObserver()
        observer.schedule(event_handler, path=self.file_monitor_settings.rclone_path, recursive=True)
        observer.start()
        return observer

    @staticmethod
    def stop_monitoring(observer):
        observer.stop()
        observer.join()
        logger.info("Stopped monitoring")