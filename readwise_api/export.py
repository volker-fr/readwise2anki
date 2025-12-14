"""Export API for fetching all data from Readwise."""

from typing import Iterator, Dict, Any, Optional


class ExportAPI:
    """API for receiving all data from Readwise."""

    def __init__(self, client):
        """Initialize the Export API.

        Args:
            client: ReadwiseClient instance
        """
        self.client = client

    def get_export_stream(
        self, updated_after: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:
        """Stream data from Readwise Export API (memory efficient).

        Results are paginated and this method handles pagination automatically.
        Yields items one at a time as they are fetched.

        Args:
            updated_after: Optional timestamp to only get data updated after this date
                          Format: ISO 8601 timestamp (e.g., "2024-01-01T00:00:00Z")

        Yields:
            Dict containing export data

        Raises:
            requests.HTTPError: If the API request fails
        """
        params = {}
        if updated_after:
            params["updatedAfter"] = updated_after

        next_page_cursor = None

        while True:
            if next_page_cursor:
                params["pageCursor"] = next_page_cursor

            response = self.client._request("GET", "/export/", params=params)
            data = response.json()

            # Yield each result
            # Its not necessary a book, even though articles have also a user_book_id
            for item in data.get("results", []):
                # stream the data.
                yield item

            # Check if there are more pages
            next_page_cursor = data.get("nextPageCursor")
            if not next_page_cursor:
                break
