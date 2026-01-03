"""Command-line interface for readwise2anki."""

import argparse
import os
import sys
import logging

from readwise_api import ReadwiseClient
from .cache import _cache_load_export
from .process import process_book
from .anki import AnkiManager


def args_parser() -> argparse.Namespace:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="readwise2anki", description="Sync Readwise highlights to Anki"
    )

    api_token_env = os.getenv("READWISE_API_TOKEN")
    parser.add_argument(
        "--api-token",
        type=str,
        default=api_token_env,
        required=api_token_env is None,
        help="Readwise API token (or set READWISE_API_TOKEN env var)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached export data instead of fetching from API (mainly for dev work)",
    )

    parser.add_argument(
        "--cache-path",
        type=str,
        default="/tmp/readwise-export.json",
        help="Path to cache file (default: /tmp/readwise-export.json)",
    )

    parser.add_argument(
        "--deck",
        type=str,
        default="Readwise::imports",
        help="Anki deck path for syncing notes (default: Readwise::imports)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the CLI."""
    args = args_parser()

    # Configure logging based on verbose flag
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        # Silence noisy third-party loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("MARKDOWN").setLevel(logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        client = ReadwiseClient(args.api_token)

        # Create the Anki manager
        anki_manager = AnkiManager(args.deck)

        # Track all highlight IDs from Readwise
        readwise_highlight_ids = set()

        if args.use_cache:
            export = _cache_load_export(client, args.cache_path)
            for item in export:
                # Collect highlight IDs
                for h in item.get("highlights", []):
                    readwise_highlight_ids.add(str(h.get("id", "")))
                process_book(item, anki_manager)
        else:
            # stream from API, more memory efficient
            for item in client.get_export_stream():
                # Collect highlight IDs
                for h in item.get("highlights", []):
                    readwise_highlight_ids.add(str(h.get("id", "")))
                process_book(item, anki_manager)

        # Sync states between Readwise and Anki
        anki_manager.sync_states(readwise_highlight_ids)

        # Save changes (AnkiConnect syncs automatically)
        anki_manager.save()

        return 0
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
