"""Tests for CLI argument parsing."""

import sys
from unittest.mock import patch
from readwise2anki.cli import args_parser


def test_no_args_shows_help():
    """Test that no arguments shows help."""
    with patch.object(sys, "argv", ["readwise2anki"]):
        args, parser = args_parser()
        assert args.command is None


def test_sync_subcommand():
    """Test sync subcommand parsing."""
    with patch.object(sys, "argv", ["readwise2anki", "sync"]):
        args, parser = args_parser()
        assert args.command == "sync"
        assert args.verbose is False
        assert args.use_cache is False


def test_sync_with_verbose():
    """Test sync with verbose flag."""
    with patch.object(sys, "argv", ["readwise2anki", "sync", "--verbose"]):
        args, parser = args_parser()
        assert args.command == "sync"
        assert args.verbose is True


def test_sync_with_api_token():
    """Test sync with API token."""
    with patch.object(sys, "argv", ["readwise2anki", "sync", "--api-token", "test-token"]):
        args, parser = args_parser()
        assert args.command == "sync"
        assert args.api_token == "test-token"


def test_sync_with_cache():
    """Test sync with cache."""
    with patch.object(sys, "argv", ["readwise2anki", "sync", "--use-cache"]):
        args, parser = args_parser()
        assert args.command == "sync"
        assert args.use_cache is True


def test_sync_with_deck():
    """Test sync with custom deck."""
    with patch.object(sys, "argv", ["readwise2anki", "sync", "--deck", "MyDeck::Subdeck"]):
        args, parser = args_parser()
        assert args.command == "sync"
        assert args.deck == "MyDeck::Subdeck"


def test_show_orphaned_subcommand():
    """Test show-orphaned subcommand."""
    with patch.object(sys, "argv", ["readwise2anki", "show-orphaned"]):
        args, parser = args_parser()
        assert args.command == "show-orphaned"


def test_delete_orphaned_subcommand():
    """Test delete-orphaned subcommand."""
    with patch.object(sys, "argv", ["readwise2anki", "delete-orphaned"]):
        args, parser = args_parser()
        assert args.command == "delete-orphaned"
        assert args.force is False


def test_delete_orphaned_with_force():
    """Test delete-orphaned with force flag."""
    with patch.object(sys, "argv", ["readwise2anki", "delete-orphaned", "--force"]):
        args, parser = args_parser()
        assert args.command == "delete-orphaned"
        assert args.force is True


def test_delete_orphaned_with_short_force():
    """Test delete-orphaned with -f flag."""
    with patch.object(sys, "argv", ["readwise2anki", "delete-orphaned", "-f"]):
        args, parser = args_parser()
        assert args.command == "delete-orphaned"
        assert args.force is True


def test_api_token_from_env(monkeypatch):
    """Test API token from environment variable."""
    monkeypatch.setenv("READWISE_API_TOKEN", "env-token")
    with patch.object(sys, "argv", ["readwise2anki", "sync"]):
        args, parser = args_parser()
        assert args.api_token == "env-token"


def test_default_deck():
    """Test default deck name."""
    with patch.object(sys, "argv", ["readwise2anki", "sync"]):
        args, parser = args_parser()
        assert args.deck == "Readwise::imports"


def test_default_cache_path():
    """Test default cache path."""
    with patch.object(sys, "argv", ["readwise2anki", "sync"]):
        args, parser = args_parser()
        assert args.cache_path == "/tmp/readwise-export.json"
