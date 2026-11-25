from unittest import mock

import pytest

from google_images_api import (
    APIError,
    AuthenticationError,
    GoogleImagesAPI,
    RateLimitError,
)


def fake_response(status=200, payload=None, json_error=False):
    response = mock.Mock()
    response.status_code = status
    response.ok = status < 400
    if json_error:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = payload
    return response


@pytest.fixture
def session():
    s = mock.Mock()
    s.headers = {}
    return s


def make_client(session):
    return GoogleImagesAPI(api_key="key", session=session)


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("COGNIFY_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        GoogleImagesAPI()


def test_api_key_from_env(monkeypatch, session):
    monkeypatch.setenv("COGNIFY_API_KEY", "envkey")
    GoogleImagesAPI(session=session)
    assert session.headers == {"x-cognifyapi-key": "envkey"}


def test_search_with_image_info(session):
    session.get.return_value = fake_response(
        payload={
            "status": "success",
            "query": "SpaceX",
            "results": 1,
            "images": [
                {
                    "url": "https://e.com/a.jpg",
                    "width": 1920,
                    "height": 1080,
                    "type": "jpg",
                    "mime": "image/jpg",
                }
            ],
        }
    )
    result = make_client(session).search("SpaceX", count=1, image_info=True)

    _, kwargs = session.get.call_args
    assert session.get.call_args[0][0] == "https://api.cognifyapi.com/google-images"
    assert kwargs["params"] == {"query": "SpaceX", "count": 1, "imageInfo": "true"}
    assert len(result) == 1
    assert result.urls == ["https://e.com/a.jpg"]
    assert result.images[0].width == 1920
    assert result.images[0].mime == "image/jpg"


def test_search_without_image_info_accepts_strings_and_objects(session):
    session.get.return_value = fake_response(
        payload={"images": ["https://e.com/a.jpg", {"url": "https://e.com/b.jpg"}]}
    )
    result = make_client(session).search("tesla")
    assert result.urls == ["https://e.com/a.jpg", "https://e.com/b.jpg"]
    assert result.images[1].width is None
    assert session.get.call_args[1]["params"] == {"query": "tesla"}


@pytest.mark.parametrize(
    "status, exc", [(401, AuthenticationError), (403, AuthenticationError),
                    (429, RateLimitError), (500, APIError)]
)
def test_http_errors(session, status, exc):
    session.get.return_value = fake_response(status, {"message": "nope"})
    with pytest.raises(exc) as info:
        make_client(session).search("x")
    assert info.value.status_code == status
    assert str(info.value) == "nope"


def test_non_json_response(session):
    session.get.return_value = fake_response(200, json_error=True)
    with pytest.raises(APIError):
        make_client(session).search("x")


def test_missing_images_array(session):
    session.get.return_value = fake_response(payload={"status": "success"})
    with pytest.raises(APIError):
        make_client(session).search("x")


@pytest.mark.parametrize("query, count", [("", None), ("  ", None), ("x", 0)])
def test_validation(session, query, count):
    with pytest.raises(ValueError):
        make_client(session).search(query, count=count)
