import httpx
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
import asyncio
from bs4 import BeautifulSoup
from tracing import trace_retriever, trace_tool

logger = logging.getLogger(__name__)

class ConfluenceConnector:
    def __init__(self, url: str, username: str, api_key: str):
        self.base_url = f"{url}/rest/api"
        self.auth = (username, api_key)
        self.client = httpx.AsyncClient(auth=self.auth, timeout=30.0)
        logger.info(f"Initialized ConfluenceConnector for {url}")

    async def close(self):
        await self.client.aclose()

    def format_cql_datetime(self, iso_time: str) -> str:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    
    def clean_confluence_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["ac:structured-macro", "ac:layout", "ac:placeholder"]):
            tag.decompose()
        return soup.get_text(separator="\n").strip()
    
    async def _request(self, endpoint: str, params: Dict = None, retries: int = 3):
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(retries):
            try:
                logger.debug(f"Requesting {url} (Attempt {attempt + 1})")
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                logger.warning(f"Request failed: {e}")
                if attempt == retries - 1:
                    logger.error(f"Max retries reached for {url}")
                    raise
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP Error: {e}")
                if attempt == retries - 1:
                    raise
        return {}

    @trace_retriever("confluence_fetch_pages")
    async def fetch_pages(self, space_key: str, updated_after: Optional[str] = None, limit: int = 50) -> List[Dict]:
        logger.info(f"Fetching pages for space {space_key} updated after {updated_after}")
        start = 0
        pages = []
        cql = f"space={space_key} AND type=page"
        if updated_after:
            cql += f" AND lastmodified > '{self.format_cql_datetime(updated_after)}'"

        while True:
            data = await self._request(
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

            async def format_task(page):
                return self._format_page_response(page)
            
            formatted_results = await asyncio.gather(*(format_task(p) for p in results))
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

    async def fetch_all_page_ids(self, space_key: str) -> set:
        logger.info(f"Fetching all page IDs for space {space_key}")
        start = 0
        limit = 100
        ids = set()
        while True:
            data = await self._request(
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
            ids.update([x["id"] for x in results])
            if len(results) < limit:
                break
            start += limit
        return ids

    @trace_retriever("confluence_fetch_page_by_id")
    async def fetch_page_by_id(self, page_id: str) -> Optional[Dict]:
        logger.info(f"Fetching page by ID: {page_id}")
        try:
            data = await self._request(f"content/{page_id}", params={"expand": "version,body.storage"})
            return self._format_page_response(data)
        except Exception as e:
            logger.error(f"Failed to fetch page {page_id}: {e}")
            return None

    @trace_tool("confluence_sync")
    async def sync(self, space_key: str, last_sync_time: Optional[str] = None, previous_page_ids: Optional[set] = None ):
        logger.info(f"Starting sync for space {space_key}")
        updated_pages, current_ids = await asyncio.gather(
            self.fetch_pages(space_key=space_key, updated_after=last_sync_time),
            self.fetch_all_page_ids(space_key)
        )

        deleted_ids = set()
        if previous_page_ids is not None:
            deleted_ids = previous_page_ids - current_ids

        new_sync_time = datetime.now(timezone.utc).isoformat()
        logger.info(f"Sync complete. Updated: {len(updated_pages)}, Deleted: {len(deleted_ids)}")

        return {
            "updated_pages": updated_pages,
            "deleted_page_ids": list(deleted_ids),
            "current_page_ids": current_ids,
            "new_sync_time": new_sync_time,
        }