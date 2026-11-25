"""Exceptions raised by google_images_api."""

from typing import Any, Optional


class GoogleImagesAPIError(Exception):
    """Base class for all errors raised by this library."""


class APIError(GoogleImagesAPIError):
    """The API returned an error response or an unexpected payload."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        payload: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class AuthenticationError(APIError):
    """The API key is missing, invalid or not allowed (HTTP 401/403)."""


class RateLimitError(APIError):
    """Too many requests or quota exceeded (HTTP 429)."""
