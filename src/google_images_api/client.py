"""HTTP client for the CognifyAPI Google Images endpoint."""

import os
import posixpath
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Union
from urllib.parse import urlparse

import requests

from .exceptions import (
    APIError,
    AuthenticationError,
    GoogleImagesAPIError,
    RateLimitError,
)

DEFAULT_BASE_URL = "https://api.cognifyapi.com"
API_KEY_ENV_VAR = "COGNIFY_API_KEY"
_EXTENSIONS = {"jpeg": "jpg"}


@dataclass
class Image:
    """A single image result.

    ``width``, ``height``, ``type`` and ``mime`` are only filled in when the
    search was made with ``image_info=True``.
    """

    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    type: Optional[str] = None
    mime: Optional[str] = None

    @classmethod
    def from_api(cls, item: Any) -> "Image":
        # Without imageInfo the API may return plain URL strings.
        if isinstance(item, str):
            return cls(url=item)
        if isinstance(item, dict) and isinstance(item.get("url"), str):
            return cls(
                url=item["url"],
                width=item.get("width"),
                height=item.get("height"),
                type=item.get("type"),
                mime=item.get("mime"),
            )
        raise APIError("Unexpected image entry in API response.", payload=item)


@dataclass
class SearchResult:
    """The parsed response of a search."""

    query: str
    images: List[Image] = field(default_factory=list)
    status: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __iter__(self) -> Iterator[Image]:
        return iter(self.images)

    def __len__(self) -> int:
        return len(self.images)

    @property
    def urls(self) -> List[str]:
        return [image.url for image in self.images]


class GoogleImagesAPI:
    """Client for ``GET /google-images``.

    >>> client = GoogleImagesAPI(api_key="YOUR_COGNIFY_API_KEY")
    >>> result = client.search("electric cars", count=10, image_info=True)
    >>> result.urls[:1]

    If ``api_key`` is omitted, the ``COGNIFY_API_KEY`` environment variable is used.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        api_key = api_key or os.environ.get(API_KEY_ENV_VAR)
        if not api_key:
            raise AuthenticationError(
                "No API key. Pass api_key=... or set the "
                f"{API_KEY_ENV_VAR} environment variable."
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.update({"x-cognifyapi-key": api_key})

    def __enter__(self) -> "GoogleImagesAPI":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def close(self) -> None:
        self._session.close()

    def search(
        self,
        query: str,
        count: Optional[int] = None,
        image_info: bool = False,
    ) -> SearchResult:
        """Search Google Images.

        :param query: Search keyword, for example ``"SpaceX"``.
        :param count: Number of results. The API default is 100.
        :param image_info: Also return width, height, type and MIME type.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string.")
        if count is not None and count < 1:
            raise ValueError("count must be a positive integer.")

        params: Dict[str, Any] = {"query": query}
        if count is not None:
            params["count"] = count
        if image_info:
            params["imageInfo"] = "true"

        data = self._get("/google-images", params)

        images = data.get("images")
        if not isinstance(images, list):
            raise APIError(
                "The API response did not contain an images array.",
                payload=data,
            )
        return SearchResult(
            query=data.get("query", query),
            images=[Image.from_api(item) for item in images],
            status=data.get("status"),
            raw=data,
        )

    def download(
        self,
        image: Union[Image, str],
        directory: str = ".",
        filename: Optional[str] = None,
    ) -> str:
        """Download one image to ``directory`` and return the file path."""
        url = image.url if isinstance(image, Image) else image
        os.makedirs(directory, exist_ok=True)
        if filename is None:
            filename = posixpath.basename(urlparse(url).path) or "image"
            if "." not in filename:
                ext = _EXTENSIONS.get(
                    (image.type or "").lower(), (image.type or "jpg").lower()
                ) if isinstance(image, Image) else "jpg"
                filename = f"{filename}.{ext}"
        path = os.path.join(directory, os.path.basename(filename))
        try:
            # Plain request: image hosts must not receive the API key header.
            response = requests.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            with open(path, "wb") as handle:
                for chunk in response.iter_content(chunk_size=65536):
                    handle.write(chunk)
        except requests.RequestException as exc:
            raise GoogleImagesAPIError(f"Could not download {url}: {exc}") from exc
        return path

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self._session.get(
                f"{self.base_url}{path}", params=params, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise GoogleImagesAPIError(f"Request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError:
            payload = None

        if response.status_code in (401, 403):
            raise AuthenticationError(
                _message(payload, "Invalid or missing API key."),
                response.status_code,
                payload,
            )
        if response.status_code == 429:
            raise RateLimitError(
                _message(payload, "Rate limit or quota exceeded."),
                response.status_code,
                payload,
            )
        if not response.ok:
            raise APIError(
                _message(payload, f"API returned HTTP {response.status_code}."),
                response.status_code,
                payload,
            )
        if not isinstance(payload, dict):
            raise APIError("API returned a non-JSON response.", response.status_code)
        return payload


def _message(payload: Any, default: str) -> str:
    if isinstance(payload, dict):
        for key in ("message", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    return default
