import os
from typing import Dict, List

import requests
from plexapi.server import PlexServer
from plexapi.library import LibrarySection
from plexapi.exceptions import BadRequest, Unauthorized
from requests.exceptions import ConnectionError as RequestsConnectionError
from urllib3.exceptions import MaxRetryError, NewConnectionError, RequestError
from loguru import logger
from settings.manager import settings_manager


class PlexUpdater:
    def __init__(self):
        self.settings = settings_manager.settings.plex
        self.library_path = settings_manager.settings.file_monitor.symlink_path
        self.plex: PlexServer = None
        self.sections: Dict[LibrarySection, List[str]] = {}
        self.initialized = self.validate()
        if not self.initialized:
            logger.error("Plex Updater failed to initialize. Changes will not be reflected in Plex.")
            return
        logger.success("Plex Updater initialized!")

    def validate(self) -> bool:
        if not self.settings.enabled:
            logger.warning("Plex Updater is set to disabled.")
            return False
        if not self.settings.token:
            logger.error("Plex token is not set!")
            return False
        if not self.settings.url:
            logger.error("Plex URL is not set!")
            return False
        if not self.library_path:
            logger.error("Library path is not set!")
            return False
        if not os.path.exists(self.library_path):
            logger.error("Library path does not exist!")
            return False

        try:
            self.plex = PlexServer(self.settings.url, self.settings.token, timeout=60)
            self.sections = self.map_sections_with_paths()
            return True
        except Unauthorized:
            logger.error("Plex is not authorized!")
        except TimeoutError as e:
            logger.error(f"Plex timeout error: {e}")
        except BadRequest:
            logger.error("Plex is not configured correctly!")
        except MaxRetryError:
            logger.error("Plex max retries exceeded")
        except NewConnectionError:
            logger.error("Plex new connection error")
        except RequestsConnectionError:
            logger.error("Plex requests connection error")
        except RequestError as e:
            logger.error(f"Plex request error: {e}")
        except Exception as e:
            logger.error(f"Plex exception thrown: {e}")
        return False

    def refresh_library(self, library_title: str) -> bool:
        try:
            library = next(lib for lib in self.plex.library.sections() if lib.title.lower() == library_title.lower())
            refresh_endpoint = f"{self.settings.url}/library/sections/{library.key}/refresh?X-Plex-Token={self.settings.token}"

            cancel_refresh_response = requests.delete(refresh_endpoint, headers={'Accept': 'application/json'})
            if cancel_refresh_response.status_code != 200:
                logger.error("Failed to cancel the refresh request")
                return False

            refresh_response = requests.get(refresh_endpoint, headers={'Accept': 'application/json'})
            if refresh_response.status_code != 200:
                logger.error("Failed to refresh the library")
                return False

            logger.success(f"Library '{library_title}' refresh initiated successfully")
            return True
        except StopIteration:
            logger.error(f"Library '{library_title}' not found")
            return False

    def map_sections_with_paths(self) -> Dict[LibrarySection, List[str]]:
        sections = [section for section in self.plex.library.sections() if
                    section.type in ["show", "movie"] and section.locations]
        return {section: section.locations for section in sections}