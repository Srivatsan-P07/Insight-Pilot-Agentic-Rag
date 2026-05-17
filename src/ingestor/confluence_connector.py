import requests
from config import AppLogger
from datetime import datetime, timezone
from typing import List, Dict, Optional
from utils import multi_thread

from datetime import datetime
from bs4 import BeautifulSoup


logger = AppLogger.setup()

class ConfluenceConnector:
    def __init__(self, url: str, username: str, api_key: str):
        self.base_url = f"{url}/rest/api"
        self.auth = (username, api_key)
        logger.app(f"Initialized ConfluenceConnector for {url}")

    def format_cql_datetime(self, iso_time: str) -> str:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    
    def clean_confluence_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted Confluence-specific tags
        for tag in soup.find_all(["ac:structured-macro", "ac:layout", "ac:placeholder"]):
            tag.decompose()

        # Extract clean text
        text = soup.get_text(separator="\n")

        return text.strip()
    
    def _request(self, endpoint: str, params: Dict = None, retries: int = 3):
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(retries):
            try:
                logger.debug(f"Requesting {url} (Attempt {attempt + 1})")
                response = requests.get(url, auth=self.auth, params=params)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.warning(f"Request failed: {e}")
                if attempt == retries - 1:
                    logger.error(f"Max retries reached for {url}")
                    raise
        return {}

    ##############################################################################################################
    def fetch_pages(self, space_key: str, updated_after: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Fetch pages optionally updated after a timestamp (ISO format).
        """
        logger.app(f"Fetching pages for space {space_key} updated after {updated_after}")
        start = 0
        pages = []

        cql = f"space={space_key} AND type=page"
        if updated_after:
            cql += f" AND lastmodified > '{self.format_cql_datetime(updated_after)}'"

        while True:
            data = self._request(
                "content/search",
                params={
                    "cql": cql,
                    "start": start,
                    "limit": limit,
                    "expand": "version,body.storage"
                },
            )

            results = data.get("results", [])
            if not results:
                break

            formatted_results = multi_thread(results, self._format_page_response)
            pages.extend(formatted_results)

            if len(results) < limit:
                break

            logger.debug(f"Fetched {len(pages)} pages so far...")
            start += limit

        return pages

    def _format_page_response(self, page: Dict) -> Dict:
        return {
            "external_id": page["id"],
            "metadata": {'title': page["title"]},
            "content": self.clean_confluence_html(page["body"]["storage"]["value"]),
            "last_updated": page["version"]["when"],
            "version": page["version"]["number"],
        }

    ##############################################################################################################
    def fetch_all_page_ids(self, space_key: str) -> set:
        """
        Used for deletion detection.
        """
        logger.app(f"Fetching all page IDs for space {space_key}")
        start = 0
        limit = 100
        ids = set()

        while True:
            data = self._request(
                "content",
                params={
                    "spaceKey": space_key,
                    "start": start,
                    "limit": limit,
                    "type": "page",
                },
            )

            results = data.get("results", [])
            if not results:
                break

            page_ids = multi_thread(results, lambda x: x["id"])
            ids.update(page_ids)

            if len(results) < limit:
                break

            start += limit

        return ids

    ##############################################################################################################
    def fetch_page_by_id(self, page_id: str) -> Optional[Dict]:
        """
        Fetch a single page by its ID.
        """
        logger.app(f"Fetching page by ID: {page_id}")
        try:
            data = self._request(f"content/{page_id}", params={"expand": "version,body.storage"})
            return self._format_page_response(data)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page {page_id}: {e}")
            return None

    ##############################################################################################################
    def sync(self, space_key: str, last_sync_time: Optional[str] = None, previous_page_ids: Optional[set] = None ):
        """
        Main sync method:
        - Fetch new/updated pages
        - Detect deletions
        """
        logger.app(f"Starting sync for space {space_key}")

        # 1. Fetch updated/new pages
        updated_pages = self.fetch_pages(
            space_key=space_key,
            updated_after=last_sync_time,
        )

        # 2. Detect deletions
        current_ids = self.fetch_all_page_ids(space_key)
        deleted_ids = set()

        if previous_page_ids is not None:
            deleted_ids = previous_page_ids - current_ids

        # 3. New sync timestamp
        new_sync_time = datetime.now(timezone.utc).isoformat()

        logger.app(f"Sync complete. Updated: {len(updated_pages)}, Deleted: {len(deleted_ids)}")

        return {
            "updated_pages": updated_pages,
            "deleted_page_ids": list(deleted_ids),
            "current_page_ids": current_ids,
            "new_sync_time": new_sync_time,
        }