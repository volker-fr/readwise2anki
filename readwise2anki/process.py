"""Processing functions for converting Readwise data to Anki."""

import logging

logger = logging.getLogger(__name__)


def process_highlight(highlight, book, anki_manager):
    """Process a single highlight.

    Args:
        highlight: Highlight data dict from Readwise export
        book: Book/article data dict from Readwise export
        anki_manager: AnkiManager instance to add the note to
    """
    if highlight.get("is_deleted", False):
        highlight_id = str(highlight.get("id", ""))
        if anki_manager.suspend_note(highlight_id):
            anki_manager.stats["notes_suspended"] += 1
            logger.debug(f"Suspended deleted highlight {highlight_id}")
        return

    anki_manager.add_note(highlight, book)


def process_book(item, anki_manager):
    """Process a single export book. Even if its an article it has a book id.

    Args:
        item: Book/article data dict from Readwise export with nested highlights
        anki_manager: AnkiManager instance to add notes to
    """
    if item.get("is_deleted", False):
        book_id = str(item.get("id", ""))
        book_title = item.get("title", "Unknown")
        suspended_count = anki_manager.suspend_book_notes(book_id, book_title)
        if suspended_count > 0:
            anki_manager.stats["books_suspended"] += 1
            anki_manager.stats["notes_suspended"] += suspended_count
            logger.debug(
                f"Suspended {suspended_count} notes from deleted book {book_id}: {book_title}"
            )
        return

    anki_manager.stats["books_processed"] += 1
    for h in item.get("highlights", []):
        process_highlight(h, item, anki_manager)
