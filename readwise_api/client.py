"""Readwise API client for querying highlights and books."""

import requests
from .export import ExportAPI


class ReadwiseClient:
    """Client for interacting with the Readwise API."""

    BASE_URL = "https://readwise.io/api/v2"

    def __init__(self, api_token: str):
        """Initialize the Readwise API client.

        Args:
            api_token: Your Readwise API token
        """
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
        )

    def export_api(self) -> ExportAPI:
        """Get the export API instance.

        Returns:
            ExportAPI instance
        """
        return ExportAPI(self)

    def get_export_stream(self, updated_after: str = None):
        """Convenience method to get export stream directly.

        Args:
            updated_after: Optional timestamp to only get data updated after this date

        Returns:
            Iterator of export data items
        """
        return self.export_api().get_export_stream(updated_after)

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
