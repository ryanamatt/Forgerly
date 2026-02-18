# src/python/services/update_checker.py

import requests
import platform
from ..utils._version import __version__
from ..utils.logger import get_logger

logger = get_logger(__name__)

class UpdateChecker:
    """
    Checks for application updates by querying the GitHub Releases API.
    
    This service compares the current application version against the latest 
    release on GitHub and determines if an update is available.
    """

    GITHUB_API_URL = "https://api.github.com/repos/ryanamatt/Forgerly/releases/latest"
    RELEASES_PAGE_URL = "https://github.com/ryanamatt/Forgerly/releases"

    def __init__(self, owner: str, repo: str, current_version: str) -> None:
        """
        Initializes the UpdateChecker with repository information.
        
        :param owner: The GitHub repository owner/organization name.
        :type owner: str
        :param repo: The GitHub repository name.
        :type repo: str
        :param current_version: The current version of the application (e.g., "0.5.0").
        :type current_version: str
        :rtype: None
        """
        self.owner = owner
        self.repo = repo
        self.current_version = current_version

    def check_for_updates(self, timeout: int = 5) -> tuple[bool, dict | None]:
        """
        Checks if a newer version is available on GitHub.
        
        This method queries the GitHub API and compares the latest release 
        version with the current application version.
        
        :param timeout: Request timeout in seconds (default: 5).
        :type timeout: int
        :returns: A tuple containing (update_available, release_info).
                 release_info is a dict with 'version', 'url', 'published_at', 
                 and 'body' keys if an update is available, None otherwise.
        :rtype: Tuple[bool, dict | None]
        """
        try:
            logger.info(f"Checking for updates at: {self.GITHUB_API_URL}")
            
            # Query GitHub API
            response = requests.get(
                self.GITHUB_API_URL,
                timeout=timeout,
                headers={'Accept': 'application/vnd.github+json'}
            )
            
            # Check if request was successful
            if response.status_code != 200:
                logger.warning(f"GitHub API returned status code {response.status_code}. "
                             f"Response: {response.text[:200]}")
                return False, None
            
            data = response.json()
            
            # Extract version from tag_name (e.g., "v0.5.0" -> "0.5.0")
            tag_name: str = data.get('tag_name', '')
            latest_version = tag_name.lstrip('v')
            
            if not latest_version:
                logger.warning("Could not extract version from GitHub release tag.")
                return False, None
                        
            logger.info(f"Latest version on GitHub: {latest_version}, Current version: {self.current_version}")
            
            # Compare versions
            if self._is_newer_version(latest_version, self.current_version):
                release_info = {
                    'version': latest_version,
                    'tag_name': tag_name,
                    'url': data.get('html_url', self.RELEASES_PAGE_URL),
                    'published_at': data.get('published_at', ''),
                    'body': data.get('body', ''),
                    'download_url': self._extract_download_url(data)
                }
                logger.info(f"Update available: v{latest_version}")
                return True, release_info
            else:
                logger.info("Application is up to date.")
                return False, None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Update check timed out after {timeout} seconds.")
            return False, None
            
        except requests.exceptions.ConnectionError:
            logger.warning("Update check failed: No internet connection or GitHub is unreachable.")
            return False, None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Update check failed due to network error: {e}", exc_info=True)
            return False, None
            
        except Exception as e:
            logger.error(f"Unexpected error during update check: {e}", exc_info=True)
            return False, None
        
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """
        Compares two semantic version strings.
        
        :param latest: The latest version string (e.g., "0.5.1").
        :type latest: str
        :param current: The current version string (e.g., "0.5.0").
        :type current: str
        :returns: True if latest is newer than current, False otherwise.
        :rtype: bool
        """
        try:
            # Convert "0.5.0" -> [0, 5, 0]
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Tuple comparison: [0, 5, 1] > [0, 5, 0] is True
            return latest_parts > current_parts

        except (ValueError, AttributeError) as e:
            logger.error(f"Invalid version parsing: {e}. Latest: {latest}, Current: {current}")
            return False
        
    def _extract_download_url(self, release_data: dict) -> list[str]:
        """
        Extracts the primary download URL from release assets.
        
        Prioritizes .exe files for Windows, then .dmg for macOS, 
        then falls back to the first asset or the release page.
        
        :param release_data: The GitHub release data dictionary.
        :type release_data: dict
        :returns: A download URL or None.
        :rtype: list[str]
        """
        assets = release_data.get('assets', [])
        sys_name = platform.system().lower()

        platform_map = {
            'windows': 'Windows.zip',
            'linux': 'Linux.zip',
            'darwin': 'macOS.zip'
        }

        target_suffix = platform_map.get(sys_name)

        if not assets:
            return release_data.get('html_url', self.RELEASES_PAGE_URL)
        
        for asset in assets:
            name = asset.get('name', '')
            if target_suffix and name.endswith(target_suffix):
                return asset.get('browser_download_url')

        return None