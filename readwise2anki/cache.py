"""Cache utilities for saving/loading Readwise data locally."""

import json
import logging
from typing import List, Dict, Any

from readwise_api import ReadwiseClient

logger = logging.getLogger(__name__)


def _cache_save_export(
    client: ReadwiseClient, file_path: str = "/tmp/readwise-export.json"
) -> None:
    """Save Readwise export data to a JSON file for dev work.

    Args:
        client: ReadwiseClient instance
        file_path: Path to save the JSON file
    """
    results = []
    for item in client.get_export_stream():
        results.append(item)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def _cache_load_export(
    client: ReadwiseClient, file_path: str = "/tmp/readwise-export.json"
) -> List[Dict[str, Any]]:
    """Load Readwise export data from a JSON file.

    If the file doesn't exist, fetches data from API and saves it.

    Args:
        client: ReadwiseClient instance (optional if cache file exists and is valid)
        file_path: Path to the JSON file

    Returns:
        List of export data items

    Raises:
        Exception: For unrecoverable errors
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        if client is None:
            raise FileNotFoundError(
                f"Cache file {file_path} does not exist and no API token provided. "
                "Please provide an API token or ensure the cache file exists."
            )
        _cache_save_export(client, file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as _:
        if client is None:
            raise ValueError(
                f"Cache file {file_path} is invalid JSON and no API token provided. "
                "Please provide an API token or ensure the cache file is valid."
            )
        _cache_save_export(client, file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (PermissionError, OSError) as e:
        logger.error(f"Cannot read cache file {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading cache file {file_path}: {e}")
        raise
