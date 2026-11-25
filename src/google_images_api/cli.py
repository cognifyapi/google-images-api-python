"""Command line interface: ``google-images-api "electric cars" -n 10``."""

import argparse
import json
import sys
from typing import List, Optional

from . import __version__
from .client import GoogleImagesAPI
from .exceptions import GoogleImagesAPIError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="google-images-api",
        description="Search Google Images through the CognifyAPI.",
    )
    parser.add_argument("query", help="search keyword")
    parser.add_argument("-n", "--count", type=int, help="number of results")
    parser.add_argument(
        "-i", "--info", action="store_true", help="include width, height and MIME type"
    )
    parser.add_argument(
        "-d", "--download", metavar="DIR", help="download the images into DIR"
    )
    parser.add_argument("--json", action="store_true", help="print the raw JSON response")
    parser.add_argument("--api-key", help="API key (default: $COGNIFY_API_KEY)")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with GoogleImagesAPI(api_key=args.api_key) as client:
            result = client.search(args.query, count=args.count, image_info=args.info)
            if args.json:
                print(json.dumps(result.raw, indent=2))
            else:
                for image in result:
                    extra = (
                        f"  {image.width}x{image.height} {image.mime}"
                        if image.width and image.height
                        else ""
                    )
                    print(f"{image.url}{extra}")
            if args.download:
                for image in result:
                    try:
                        print("saved", client.download(image, args.download), file=sys.stderr)
                    except GoogleImagesAPIError as exc:
                        print(f"skipped: {exc}", file=sys.stderr)
    except (GoogleImagesAPIError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
