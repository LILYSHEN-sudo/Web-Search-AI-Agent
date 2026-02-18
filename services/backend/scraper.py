import json
from typing import Optional
from urllib.parse import quote_plus

import httpx

from config import settings

BASE_URL = "https://api.brightdata.com/request"


class ScraperError(Exception):
    """Exception raised for scraper API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SearchResult:
    def __init__(self, title: str, url: str, description: str):
        self.title = title
        self.url = url
        self.description = description

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
        }


class ScraperClient:
    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: str = BASE_URL,
    ):
        self.api_token = api_token or settings.brightdata_api_token
        self.base_url = base_url

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _parse_search_results(self, data: dict) -> list[SearchResult]:
        """Parse BrightData response into SearchResult objects."""
        # BrightData returns {status_code, headers, body}
        body = data.get("body", data)

        # Body might be a JSON string that needs parsing
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return []

        # Look for organic results in different possible locations
        organic = body.get("organic") or body.get("organic_results") or []

        results = []
        for item in organic:
            title = item.get("title", "")
            url = item.get("link") or item.get("url", "")
            description = item.get("description") or item.get("snippet", "")

            if title and url:
                results.append(SearchResult(title=title, url=url, description=description))

        return results

    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search Google using BrightData's SERP API.

        Args:
            query: The search query string.
            num_results: Number of results to return (default 10).

        Returns:
            List of SearchResult objects.

        Raises:
            ScraperError: If the API request fails.
        """
        # URL-encode the query for the Google search URL
        encoded_query = quote_plus(query)
        google_url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"

        payload = {
            "zone": "serp_api1",
            "format": "json",
            "data_format": "parsed_light",
            "url": google_url,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=self._get_headers(),
                    json=payload,
                )

                if response.status_code != 200:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", error_detail)
                    except Exception:
                        pass
                    raise ScraperError(
                        f"API request failed: {error_detail}",
                        status_code=response.status_code,
                    )

                data = response.json()
                return self._parse_search_results(data)

        except httpx.TimeoutException:
            raise ScraperError("Request timed out")
        except httpx.RequestError as e:
            raise ScraperError(f"Request failed: {str(e)}")

    async def search_as_dict(self, query: str, num_results: int = 10) -> list[dict]:
        """Search and return results as dictionaries."""
        results = await self.search(query, num_results)
        return [r.to_dict() for r in results]


scraper_client = ScraperClient()
