import requests
from typing import Dict, List, Optional
from urllib.parse import urljoin

class ConfluenceConnector:
  """Connector for interacting with Confluence API."""
  
  def __init__(self, base_url: str, username: str, api_token: str):
    """
    Initialize Confluence connector.
    
    Args:
      base_url: Confluence instance URL (e.g., https://company.atlassian.net/wiki)
      username: Atlassian username
      api_token: Atlassian API token
    """
    self.base_url = base_url
    self.auth = (username, api_token)
    self.headers = {"Accept": "application/json"}
  
  def get_pages_updated_after(self, timestamp: str, space_key: Optional[str] = None) -> List[Dict]:
    """
    Get all pages updated after a given timestamp.
    
    Args:
      timestamp: ISO 8601 timestamp (e.g., '2024-01-01T00:00:00.000Z')
      space_key: Optional Confluence space key to filter results
    
    Returns:
      List of pages updated after the timestamp
    """
    url = urljoin(self.base_url, "rest/api/content/search")
    space_filter = f'space = "{space_key}" and ' if space_key else ""
    cql_query = f'{space_filter}lastModified >= "{timestamp}" order by lastModified desc'
    params = {"cql": cql_query}
    response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
    response.raise_for_status()
    return response.json().get("results", [])
  
  def get_page_by_id(self, page_id: str, expand: Optional[str] = None) -> Dict:
      """
      Get page content by ID.
      
      Args:
        page_id: Confluence page ID
        expand: Optional fields to expand (e.g., 'body.storage')
      
      Returns:
        Page content as a dictionary
      """
      url = urljoin(self.base_url, f"rest/api/content/{page_id}")
      params = {"expand": expand} if expand else {}
      response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
      response.raise_for_status()
      return response.json()