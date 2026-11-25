import json
from unittest import mock

from google_images_api import cli
from google_images_api.client import Image, SearchResult


def test_cli_prints_urls(capsys, monkeypatch):
    monkeypatch.setenv("COGNIFY_API_KEY", "key")
    result = SearchResult(
        query="x",
        images=[Image(url="https://e.com/a.jpg", width=10, height=20, mime="image/jpg")],
        raw={"images": []},
    )
    with mock.patch("google_images_api.cli.GoogleImagesAPI") as cls:
        cls.return_value.__enter__.return_value.search.return_value = result
        assert cli.main(["x", "-n", "1", "-i"]) == 0
    assert "https://e.com/a.jpg  10x20 image/jpg" in capsys.readouterr().out


def test_cli_json(capsys, monkeypatch):
    monkeypatch.setenv("COGNIFY_API_KEY", "key")
    result = SearchResult(query="x", images=[], raw={"status": "success"})
    with mock.patch("google_images_api.cli.GoogleImagesAPI") as cls:
        cls.return_value.__enter__.return_value.search.return_value = result
        assert cli.main(["x", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"status": "success"}


def test_cli_missing_key(capsys, monkeypatch):
    monkeypatch.delenv("COGNIFY_API_KEY", raising=False)
    assert cli.main(["x"]) == 1
    assert "No API key" in capsys.readouterr().err
