# google-images-api by cognifyapi

[![PyPI version](https://img.shields.io/pypi/v/google-images-api.svg)](https://pypi.org/project/google-images-api/)
[![Python versions](https://img.shields.io/pypi/pyversions/google-images-api.svg)](https://pypi.org/project/google-images-api/)
[![License: MIT](https://img.shields.io/pypi/l/google-images-api.svg)](https://github.com/cognifyapi/google-images-api-python/blob/main/LICENSE)


A small Python client for the [CognifyAPI Google Images API](https://cognifyapi.com/google-images).
Search Google Images and get structured JSON back: image URLs, plus width, height and MIME type with JSON results.

**[Get an API key (free trial)](https://studio.cognifyapi.com/)**

## Install

```bash
pip install google-images-api
```

Requires Python 3.10 or newer.

## Quickstart

```python
from google_images_api import GoogleImagesAPI

client = GoogleImagesAPI(api_key="YOUR_COGNIFY_API_KEY")
result = client.search("electric cars", count=10)

for image in result:
    print(image.url)
```

You can also set the key once in your environment and omit `api_key`:

```bash
export COGNIFY_API_KEY="YOUR_COGNIFY_API_KEY"
```

## Usage

### Image metadata

```python
result = client.search("SpaceX", count=5, image_info=True)

for image in result:
    print(image.url, image.width, image.height, image.type, image.mime)
```

Without `image_info=True`, only `image.url` is filled in.

### Just the URLs

```python
urls = client.search("tesla", count=20).urls
```

### Download images

```python
for image in client.search("northern lights", count=3):
    path = client.download(image, directory="images")
    print("saved", path)
```

### Raw JSON

```python
result.raw          # the full API response as a dict
result.status       # "success"
```

### Use as a context manager

```python
with GoogleImagesAPI() as client:
    print(client.search("sunset").urls)
```

### Error handling

```python
from google_images_api import AuthenticationError, RateLimitError, APIError, GoogleImagesAPIError

try:
    client.search("cats")
except AuthenticationError:
    ...   # bad or missing API key
except RateLimitError:
    ...   # too many requests or quota used up
except APIError as exc:
    print(exc.status_code, exc)
except GoogleImagesAPIError:
    ...   # network problem or any other library error
```

## Command line

```bash
google-images-api "electric cars" -n 10             # print image URLs
google-images-api "SpaceX" -n 5 --info              # with width, height and MIME type
google-images-api "tesla" -n 5 --download ./images  # save the files
google-images-api "tesla" --json                    # raw JSON
```

## API reference

`GoogleImagesAPI(api_key=None, base_url="https://api.cognifyapi.com", timeout=30.0)`

`client.search(query, count=None, image_info=False) -> SearchResult`

| Parameter    | Required | Description                                              |
| ------------ | -------- | -------------------------------------------------------- |
| `query`      | yes      | Search keyword, for example `"SpaceX"`.                  |
| `count`      | no       | Number of results (API default: 100).                    |
| `image_info` | no       | Also return width, height, type and MIME type.           |

Example API response:

```json
{
  "status": "success",
  "query": "SpaceX",
  "results": 2,
  "images": [
    { "url": "https://example.com/image.jpg", "width": 1920, "height": 1080, "type": "jpg", "mime": "image/jpg" }
  ]
}
```

## Development

```bash
git clone https://github.com/cognifyapi/google-images-api-python.git
cd google-images-api-python
pip install -e ".[dev]"
pytest
```

## Links

- [API documentation](https://cognifyapi.com/docs/google-images-docs)
- [Google Images API](https://cognifyapi.com/google-images)
- [CognifyAPI](https://cognifyapi.com/)
- [Report an issue](https://github.com/cognifyapi/google-images-api-python/issues)

## License

MIT. See [LICENSE](LICENSE).
