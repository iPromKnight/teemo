import os
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from urllib3.exceptions import MaxRetryError, NewConnectionError, RequestError
from loguru import logger
from settings.manager import settings_manager


class AudiobookShelfUpdater:
    def __init__(self):
        self.settings = settings_manager.settings.audiobookshelf
        self.library_path = settings_manager.settings.file_monitor.symlink_path
        self.base_url = self.settings.url
        self.token = self.settings.token
        self.folder_to_library_id = self.settings.folder_to_library_id
        self.initialized = self.validate()
        if not self.initialized:
            logger.error("AudiobookShelf Updater failed to initialize. Changes will not be reflected in AudiobookShelf.")
            return
        logger.success("AudiobookShelf Updater initialized!")

    def validate(self) -> bool:
        if not self.settings.enabled:
            logger.warning("AudiobookShelf Updater is set to disabled.")
            return False
        if not self.token:
            logger.error("AudiobookShelf token is not set!")
            return False
        if not self.base_url:
            logger.error("AudiobookShelf URL is not set!")
            return False
        if not self.library_path:
            logger.error("Library path is not set!")
            return False
        if not os.path.exists(self.library_path):
            logger.error("Library path does not exist!")
            return False

        try:
            response = requests.get(f"{self.base_url}/api/v1/auth/validate", headers={"Authorization": f"Bearer {self.token}"})
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            logger.error(f"AudiobookShelf HTTP error: {e}")
        except MaxRetryError:
            logger.error("AudiobookShelf max retries exceeded")
        except NewConnectionError:
            logger.error("AudiobookShelf new connection error")
        except RequestsConnectionError:
            logger.error("AudiobookShelf requests connection error")
        except RequestError as e:
            logger.error(f"AudiobookShelf request error: {e}")
        except Exception as e:
            logger.error(f"AudiobookShelf exception thrown: {e}")
        return False

    def refresh_library(self, folder_path: str) -> bool:
        library_id = self.folder_to_library_id.get(folder_path)
        if not library_id:
            logger.error(f"Library ID not found for folder path: {folder_path}")
            return False

        try:
            refresh_endpoint = f"{self.base_url}/api/v1/libraries/{library_id}/scan"
            response = requests.post(refresh_endpoint, headers={"Authorization": f"Bearer {self.token}"})
            response.raise_for_status()
            logger.success(f"Library refresh for '{folder_path}' initiated successfully")
            return True
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to refresh the library for '{folder_path}': {e}")
            return False
        except Exception as e:
            logger.error(f"Exception occurred while refreshing the library for '{folder_path}': {e}")
            return False
