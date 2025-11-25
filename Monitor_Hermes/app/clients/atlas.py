import httpx
from typing import Optional, Dict, Any
from app.settings import settings
import loguru


class AtlasClient:
    """
    HTTP client to interact with the Atlas API.
    Automatically handles authentication via X-API-Key.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the Atlas client.

        Args:
            base_url: Base URL of the Atlas API. If not provided, uses ATLAS_HOST_URL from settings.
            api_key: API Key for authentication. If not provided, uses SERVICE_API_KEY from settings.
        """
        self.base_url = base_url or settings.ATLAS_HOST_URL
        self.api_key = api_key or settings.SERVICE_API_KEY
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def _get_full_url(self, endpoint: str) -> str:
        """
        Build the full URL by combining base_url with the endpoint.

        Args:
            endpoint: API endpoint (must start with /)

        Returns:
            Full URL
        """
        return f"{self.base_url.rstrip('/')}{endpoint}"

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> httpx.Response:
        """
        Perform a GET request to the Atlas API.

        Args:
            endpoint: API endpoint (e.g., /api/v1/devices)
            params: Query string parameters
            headers: Additional headers (merged with default headers)
            timeout: Timeout in seconds

        Returns:
            httpx Response

        Raises:
            httpx.HTTPError: If there is any request error
        """
        url = self._get_full_url(endpoint)
        request_headers = {**self.headers, **(headers or {})}

        async with httpx.AsyncClient(timeout=timeout) as client:
            loguru.logger.debug(f"GET request to {url} with params: {params}")
            response = await client.get(url, params=params, headers=request_headers)
            response.raise_for_status()
            return response

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> httpx.Response:
        """
        Perform a POST request to the Atlas API.

        Args:
            endpoint: API endpoint (e.g., /api/v1/devices)
            data: Data to send as form data
            json: Data to send as JSON
            headers: Additional headers (merged with default headers)
            timeout: Timeout in seconds

        Returns:
            httpx Response

        Raises:
            httpx.HTTPError: If there is any request error
        """
        url = self._get_full_url(endpoint)
        request_headers = {**self.headers, **(headers or {})}

        async with httpx.AsyncClient(timeout=timeout) as client:
            loguru.logger.debug(f"POST request to {url}")
            response = await client.post(
                url, data=data, json=json, headers=request_headers
            )
            response.raise_for_status()
            return response

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> httpx.Response:
        """
        Perform a PUT request to the Atlas API.

        Args:
            endpoint: API endpoint (e.g., /api/v1/devices/123)
            data: Data to send as form data
            json: Data to send as JSON
            headers: Additional headers (merged with default headers)
            timeout: Timeout in seconds

        Returns:
            httpx Response

        Raises:
            httpx.HTTPError: If there is any request error
        """
        url = self._get_full_url(endpoint)
        request_headers = {**self.headers, **(headers or {})}

        async with httpx.AsyncClient(timeout=timeout) as client:
            loguru.logger.debug(f"PUT request to {url}")
            response = await client.put(
                url, data=data, json=json, headers=request_headers
            )
            response.raise_for_status()
            return response

    async def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> httpx.Response:
        """
        Perform a PATCH request to the Atlas API.

        Args:
            endpoint: API endpoint (e.g., /api/v1/devices/123)
            data: Data to send as form data
            json: Data to send as JSON
            headers: Additional headers (merged with default headers)
            timeout: Timeout in seconds

        Returns:
            httpx Response

        Raises:
            httpx.HTTPError: If there is any request error
        """
        url = self._get_full_url(endpoint)
        request_headers = {**self.headers, **(headers or {})}

        async with httpx.AsyncClient(timeout=timeout) as client:
            loguru.logger.debug(f"PATCH request to {url}")
            response = await client.patch(
                url, data=data, json=json, headers=request_headers
            )
            response.raise_for_status()
            return response

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> httpx.Response:
        """
        Perform a DELETE request to the Atlas API.

        Args:
            endpoint: API endpoint (e.g., /api/v1/devices/123)
            params: Query string parameters
            headers: Additional headers (merged with default headers)
            timeout: Timeout in seconds

        Returns:
            httpx Response

        Raises:
            httpx.HTTPError: If there is any request error
        """
        url = self._get_full_url(endpoint)
        request_headers = {**self.headers, **(headers or {})}

        async with httpx.AsyncClient(timeout=timeout) as client:
            loguru.logger.debug(f"DELETE request to {url}")
            response = await client.delete(url, params=params, headers=request_headers)
            response.raise_for_status()
            return response


# Singleton instance of the client for reuse across the application
atlas_client = AtlasClient()
