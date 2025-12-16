# src/composers/pexels_client.py
"""Pexels API client for stock images.

Pexels offers free, high-quality curated stock photos with a simple API.
Rate limit: 200 requests/hour, 20,000/month (can request unlimited).
"""

import os
import time
from typing import Optional

import httpx

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PexelsClient:
    """
    Client for Pexels stock photo API.

    Pexels is free and provides high-quality curated images.
    Good replacement for Unsplash with similar API structure.
    """

    API_URL = "https://api.pexels.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Pexels client.

        Args:
            api_key: Pexels API key (get free at https://www.pexels.com/api/)
        """
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")

        if not self.api_key:
            logger.warning("PEXELS_API_KEY not set - Pexels integration unavailable")

        self.client = httpx.Client(
            headers={"Authorization": self.api_key} if self.api_key else {},
            timeout=30.0,
        )

    @property
    def is_available(self) -> bool:
        """Check if Pexels API is configured."""
        return self.api_key is not None

    def search(
        self,
        query: str,
        per_page: int = 10,
        page: int = 1,
        orientation: Optional[str] = "landscape",
        size: Optional[str] = "large",
    ) -> list[dict]:
        """
        Search for photos on Pexels.

        Args:
            query: Search query
            per_page: Results per page (max 80)
            page: Page number
            orientation: landscape, portrait, or square
            size: large, medium, or small

        Returns:
            List of photo dictionaries
        """
        if not self.is_available:
            logger.warning("Pexels API not available")
            return []

        params = {
            "query": query,
            "per_page": min(per_page, 80),
            "page": page,
        }

        if orientation:
            params["orientation"] = orientation
        if size:
            params["size"] = size

        try:
            response = self.client.get(f"{self.API_URL}/search", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("photos", [])
        except httpx.HTTPStatusError as e:
            logger.error(f"Pexels API error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Pexels search failed: {e}")
            return []

    def get_curated(self, per_page: int = 10, page: int = 1) -> list[dict]:
        """
        Get curated photos (Pexels' featured selection).

        Args:
            per_page: Results per page
            page: Page number

        Returns:
            List of curated photos
        """
        if not self.is_available:
            return []

        try:
            response = self.client.get(
                f"{self.API_URL}/curated",
                params={"per_page": per_page, "page": page},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("photos", [])
        except Exception as e:
            logger.error(f"Pexels curated fetch failed: {e}")
            return []

    def get_photo(self, photo_id: int) -> Optional[dict]:
        """
        Get a specific photo by ID.

        Args:
            photo_id: Pexels photo ID

        Returns:
            Photo dictionary or None
        """
        if not self.is_available:
            return None

        try:
            response = self.client.get(f"{self.API_URL}/photos/{photo_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Pexels photo fetch failed: {e}")
            return None

    def format_for_matcher(self, photo: dict) -> dict:
        """
        Convert Pexels photo format to match Unsplash format.

        This allows the ImageMatcher to use Pexels photos with minimal changes.

        Args:
            photo: Pexels photo dictionary

        Returns:
            Dictionary in Unsplash-compatible format
        """
        return {
            "id": str(photo["id"]),
            "width": photo["width"],
            "height": photo["height"],
            "color": photo.get("avg_color", "#808080"),
            "urls": {
                "regular": photo["src"]["large"],
                "thumb": photo["src"]["small"],
                "full": photo["src"]["original"],
            },
            "user": {
                "name": photo.get("photographer", "Unknown"),
                "links": {
                    "html": photo.get("photographer_url", "https://pexels.com"),
                },
            },
            "likes": 0,  # Pexels doesn't expose likes
            "source": "pexels",
        }

    def close(self):
        """Close HTTP client."""
        self.client.close()


# Singleton instance
_client: Optional[PexelsClient] = None


def get_pexels_client() -> PexelsClient:
    """Get or create Pexels client singleton."""
    global _client
    if _client is None:
        _client = PexelsClient()
    return _client
