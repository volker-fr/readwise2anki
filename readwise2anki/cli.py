"""Command-line interface for readwise2anki."""

import argparse
import os
import sys
import logging

from readwise_api import ReadwiseClient
from .cache import _cache_load_export
from .process import process_book
from .anki import AnkiManager


def args_parser() -> tuple[argparse.Namespace, argparse.ArgumentParser]:
    """Create the argument parser.

    Returns:
        Tuple of (parsed args, parser instance)
    """
    parser = argparse.ArgumentParser(
        prog="readwise2anki", description="Sync Readwise highlights to Anki"
    )

    # Common arguments
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

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create parent parser with common arguments for subcommands
    # This allows flags to work both before and after the subcommand
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--api-token",
        type=str,
        default=api_token_env,
        help="Readwise API token (or set READWISE_API_TOKEN env var)",
    )
    parent_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parent_parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached export data instead of fetching from API (mainly for dev work)",
    )
    parent_parser.add_argument(
        "--cache-path",
        type=str,
        default="/tmp/readwise-export.json",
        help="Path to cache file (default: /tmp/readwise-export.json)",
    )
    parent_parser.add_argument(
        "--deck",
        type=str,
        default="Readwise::imports",
        help="Anki deck path for syncing notes (default: Readwise::imports)",
    )

    # sync subcommand
    subparsers.add_parser(
        "sync",
        help="Sync Readwise highlights to Anki (default)",
        parents=[parent_parser],
    )

    # show-orphaned subcommand
    subparsers.add_parser(
        "show-orphaned",
        help="Show orphaned notes (notes in Anki but not in Readwise)",
        parents=[parent_parser],
    )

    # delete-orphaned subcommand
    subparsers.add_parser(
        "delete-orphaned",
        help="Delete orphaned notes (notes in Anki but not in Readwise)",
        parents=[parent_parser],
    )

    return parser.parse_args(), parser


def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbose flag."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        # Silence noisy third-party loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("MARKDOWN").setLevel(logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_readwise_highlights(
    client: ReadwiseClient, use_cache: bool, cache_path: str, anki_manager: AnkiManager
) -> set:
    """Load highlights from Readwise and process them.

    Args:
        client: ReadwiseClient instance
        use_cache: Whether to use cached export data
        cache_path: Path to cache file
        anki_manager: AnkiManager instance

    Returns:
        Set of all highlight IDs from Readwise
    """
    readwise_highlight_ids = set()

    if use_cache:
        export = _cache_load_export(client, cache_path)
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

    return readwise_highlight_ids


def main() -> int:
    """Main entry point for the CLI."""
    args, parser = args_parser()

    # Show help if no command is provided
    if not args.command:
        parser.print_help()
        return 0

    configure_logging(args.verbose)

    try:
        client = ReadwiseClient(args.api_token)
        anki_manager = AnkiManager(args.deck)

        if args.command == "sync":
            # Normal sync behavior - just sync highlights, no orphan detection
            load_readwise_highlights(
                client, args.use_cache, args.cache_path, anki_manager
            )
            anki_manager.save()

        elif args.command == "show-orphaned":
            # Show orphaned notes with details
            readwise_highlight_ids = load_readwise_highlights(
                client, args.use_cache, args.cache_path, anki_manager
            )
            anki_manager.handle_orphaned_notes(
                readwise_highlight_ids, show_details=True, delete=False
            )

        elif args.command == "delete-orphaned":
            # Delete orphaned notes
            readwise_highlight_ids = load_readwise_highlights(
                client, args.use_cache, args.cache_path, anki_manager
            )
            anki_manager.handle_orphaned_notes(
                readwise_highlight_ids, show_details=True, delete=True
            )

        return 0
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
