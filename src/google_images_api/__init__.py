"""Python client for the CognifyAPI Google Images API."""

from .client import GoogleImagesAPI, Image, SearchResult
from .exceptions import (
    APIError,
    AuthenticationError,
    GoogleImagesAPIError,
    RateLimitError,
)

__version__ = "0.1.0"

__all__ = [
    "GoogleImagesAPI",
    "Image",
    "SearchResult",
    "GoogleImagesAPIError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "__version__",
]
