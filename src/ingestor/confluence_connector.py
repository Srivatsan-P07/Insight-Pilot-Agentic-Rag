import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

from datetime import datetime
from bs4 import BeautifulSoup

class ConfluenceConnector:
    def __init__(self, url: str, username: str, api_key: str):
        self.base_url = f"{url}/rest/api"
        self.auth = (username, api_key)

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
                response = requests.get(url, auth=self.auth, params=params)
                response.raise_for_status()
                return response.json()
            except requests.RequestException:
                if attempt == retries - 1:
                    raise
        return {}

    ##############################################################################################################
    def fetch_pages(self, space_key: str, updated_after: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Fetch pages optionally updated after a timestamp (ISO format).
        """
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

            for page in results:
                pages.append({
                    "external_id": page["id"],
                    "metadata": {'title': page["title"]},
                    "content": self.clean_confluence_html(page["body"]["storage"]["value"]),
                    "last_updated": page["version"]["when"],
                    "version": page["version"]["number"],
                })

            if len(results) < limit:
                break

            start += limit

        return pages

    ##############################################################################################################
    def fetch_all_page_ids(self, space_key: str) -> set:
        """
        Used for deletion detection.
        """
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

            for page in results:
                ids.add(page["id"])

            if len(results) < limit:
                break

            start += limit

        return ids

    ##############################################################################################################
    def fetch_page_by_id(self, page_id: str) -> Optional[Dict]:
        """
        Fetch a single page by its ID.
        """
        try:
            data = self._request(f"content/{page_id}", params={"expand": "version,body.storage"})
            return {
                "external_id": data["id"],
                "metadata": {'title': data["title"]},
                "content": self.clean_confluence_html(data["body"]["storage"]["value"]),
                "last_updated": data["version"]["when"],
                "version": data["version"]["number"],
            }
        except requests.RequestException:
            return None

    ##############################################################################################################
    def sync(self, space_key: str, last_sync_time: Optional[str] = None, previous_page_ids: Optional[set] = None ):
        """
        Main sync method:
        - Fetch new/updated pages
        - Detect deletions
        """

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

        return {
            "updated_pages": updated_pages,
            "deleted_page_ids": list(deleted_ids),
            "current_page_ids": current_ids,
            "new_sync_time": new_sync_time,
        }