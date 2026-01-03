"""Anki deck and note management using AnkiConnect."""

import requests
import logging
from typing import Optional, Any
from textwrap import dedent
import markdown

logger = logging.getLogger(__name__)


class AnkiConnectError(Exception):
    """Exception raised for AnkiConnect API errors."""

    pass


class AnkiManager:
    """Manages Anki deck creation and note addition via AnkiConnect."""

    # Model schema - single source of truth
    MODEL_FIELDS = [
        "Text",
        "Title",
        "Author",
        "Source",
        "Category",
        "Note",
        "Tags",
        "HighlightID",
        "UpdatedAt",
        "HighlightURL",
        "ReadwiseURL",
        "Color",
        "IsFavorite",
    ]

    MODEL_CSS = """
        .card {
            font-family: arial;
            text-align: left;
            color: black;
            background-color: white;
        }
        .highlight {
            margin-bottom: 20px;
            line-height: 1.4;
        }
        .source {
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }
        .metadata {
            color: #555;
        }
        .metadata div {
            margin: 5px 0;
        }
        .note {
            margin-top: 15px;
            padding: 10px;
            background-color: #f0f0f0;
            border-left: 3px solid #4CAF50;
        }
        .color-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
        }
        .favorite-icon {
            color: red;
            margin-left: 8px;
        }
        .url-link {
            word-break: break-all;
        }
    """

    TEMPLATE_FRONT = """<div class="highlight">{{Text}}</div>
<div class="source">— {{Title}}</div>"""

    TEMPLATE_BACK = """{{FrontSide}}
<hr id="answer">
<div class="metadata">
    <div><strong>Author:</strong> {{Author}}</div>
    <div><strong>Source:</strong> {{Source}}</div>
    <div><strong>Category:</strong> {{Category}}</div>
    {{#Note}}<div class="note"><strong>Note:</strong> {{Note}}</div>{{/Note}}
    {{#HighlightURL}}<div class="url-link"><a href="{{HighlightURL}}" target="_blank">View Source ↗</a></div>{{/HighlightURL}}
    {{#ReadwiseURL}}<div><a href="{{ReadwiseURL}}" target="_blank">On Readwise.com ↗</a></div>{{/ReadwiseURL}}
    <div>{{#IsFavorite}}<span class="favorite-icon">❤️</span>{{/IsFavorite}}{{#Color}}<span class="color-indicator" style="background-color: {{Color}};"></span>{{/Color}}</div>
</div>"""

    def __init__(
        self,
        deck_name: str = "Readwise",
        anki_connect_url: str = "http://localhost:8765",
    ):
        """Initialize the Anki manager with AnkiConnect.

        Args:
            deck_name: Name of the deck
            anki_connect_url: URL of AnkiConnect API
        """
        self.deck_name = deck_name
        self.anki_connect_url = anki_connect_url
        self.model_name = "Readwise Highlight"
        self.stats = {
            "books_processed": 0,
            "books_suspended": 0,
            "highlights_processed": 0,
            "notes_added": 0,
            "notes_updated": 0,
            "notes_suspended": 0,
            "notes_skipped": 0,
            "notes_orphaned": 0,
            "notes_deleted": 0,
        }

        # Ensure Anki is running and AnkiConnect is available
        self._check_anki_connect()

        # Create deck if it doesn't exist
        self._create_deck_if_needed()

    def _configure_deck_preset(self):
        """Configure deck with its own preset for learning intervals."""
        preset_name = "Readwise Learning"

        # Get current deck config
        current_config = self._invoke("getDeckConfig", deck=self.deck_name)

        if not current_config:
            return

        current_name = current_config.get("name", "")
        current_config_id = current_config.get("id")

        # If already using our preset, just update it if needed
        if current_name == preset_name:
            current_delays = current_config["new"].get("delays", [])
            target_delays = [4320, 14400, 43200]

            if current_delays != target_delays:
                current_config["new"]["delays"] = target_delays
                current_config["new"]["ints"] = [30, 30]
                current_config["rev"]["ease4"] = 1.3
                self._invoke("saveDeckConfig", config=current_config)
                logger.info(f"Updated deck preset '{preset_name}' learning steps")
            return

        # Need to create new preset - clone the current one
        new_config_id = self._invoke(
            "cloneDeckConfigId", name=preset_name, cloneFrom=current_config_id
        )

        # Get the newly created config
        self._invoke("setDeckConfigId", decks=[self.deck_name], configId=new_config_id)
        new_config = self._invoke("getDeckConfig", deck=self.deck_name)

        # Configure the learning steps
        new_config["new"]["delays"] = [4320, 14400, 43200]  # in minutes: 3d, 10d, 30d
        new_config["new"]["ints"] = [30, 30]  # graduating and easy interval in days
        new_config["rev"]["ease4"] = 1.3  # Easy bonus 130%

        # Save the updated config
        self._invoke("saveDeckConfig", config=new_config)

        logger.info(
            f"Created deck preset '{preset_name}' with learning steps: 3 days, 10 days, 30 days"
        )

    def _invoke(self, action: str, **params) -> Any:
        """Invoke AnkiConnect API.

        Args:
            action: AnkiConnect action name
            **params: Parameters for the action

        Returns:
            Result from AnkiConnect

        Raises:
            AnkiConnectError: If the request fails
        """
        payload = {"action": action, "version": 6, "params": params}

        try:
            response = requests.post(self.anki_connect_url, json=payload)
            response.raise_for_status()
            result = response.json()

            if len(result) != 2:
                raise AnkiConnectError("Response has unexpected number of fields")
            if "error" not in result:
                raise AnkiConnectError("Response is missing required error field")
            if "result" not in result:
                raise AnkiConnectError("Response is missing required result field")
            if result["error"] is not None:
                raise AnkiConnectError(result["error"])

            return result["result"]
        except requests.exceptions.RequestException as e:
            raise AnkiConnectError(f"Failed to connect to AnkiConnect: {e}")

    def _check_anki_connect(self):
        """Check if AnkiConnect is available."""
        try:
            self._invoke("version")
        except AnkiConnectError as e:
            raise AnkiConnectError(
                f"Cannot connect to Anki. Make sure Anki is running and AnkiConnect add-on is installed. Error: {e}"
            )

    def _create_deck_if_needed(self):
        """Create the deck if it doesn't exist."""
        self._invoke("createDeck", deck=self.deck_name)

        # Try to configure deck with its own preset
        try:
            self._configure_deck_preset()
        except AnkiConnectError as e:
            logger.debug(f"Could not configure deck preset: {e}")
        
        # Always check model, regardless of preset configuration
        self._create_model_if_needed()

    def _create_model_if_needed(self):
        """Create the custom model if it doesn't exist."""
        # Check if model already exists
        model_names = self._invoke("modelNames")
        if self.model_name in model_names:
            # Model exists, validate schema (AnkiConnect API doesn't support auto-updates)
            self._validate_model_schema()
            return

        # Create the model using class constants
        model = {
            "modelName": self.model_name,
            "inOrderFields": self.MODEL_FIELDS,
            "css": self.MODEL_CSS,
            "cardTemplates": [
                {
                    "Name": "Card 1",
                    "Front": self.TEMPLATE_FRONT,
                    "Back": self.TEMPLATE_BACK,
                }
            ],
        }

        self._invoke("createModel", **model)
        logger.info(f"Created model '{self.model_name}'")

    def _validate_model_schema(self):
        """Validate model schema and warn if manual updates needed.

        Note: AnkiConnect API doesn't support automatic model updates,
        so this method only validates and warns the user.
        """
        try:
            # Get current fields
            current_fields = self._invoke("modelFieldNames", modelName=self.model_name)

            # Check for missing fields using class constant
            missing_fields = [f for f in self.MODEL_FIELDS if f not in current_fields]

            if missing_fields:
                logger.warning(dedent(f"""\
                    Model '{self.model_name}' is missing fields: {', '.join(missing_fields)}

                    To add missing fields without losing data:
                      1. Open Anki → Tools → Manage Note Types
                      2. Select '{self.model_name}' → Fields
                      3. Click 'Add' and create each missing field: {', '.join(missing_fields)}
                      4. Then update the card template (Cards button) to show the new fields

                    Note: New fields will be empty for existing cards, but will populate for future syncs"""))

            # Check if card templates need updating using class constants
            try:
                # Get current model templates
                model_templates = self._invoke("modelTemplates", modelName=self.model_name)

                # Normalize whitespace for comparison
                current_front = " ".join(model_templates.get("Card 1", {}).get("Front", "").split())
                current_back = " ".join(model_templates.get("Card 1", {}).get("Back", "").split())
                expected_front_norm = " ".join(self.TEMPLATE_FRONT.split())
                expected_back_norm = " ".join(self.TEMPLATE_BACK.split())

                if current_front != expected_front_norm or current_back != expected_back_norm:
                    templates_to_show = []
                    if current_front != expected_front_norm:
                        templates_to_show.append(f"Front template:\n{self.TEMPLATE_FRONT.strip()}")
                    if current_back != expected_back_norm:
                        templates_to_show.append(f"Back template:\n{self.TEMPLATE_BACK.strip()}")

                    logger.warning(dedent(f"""\
                        Model '{self.model_name}' card template differs from expected

                        To update the template:
                          1. Open Anki → Tools → Manage Note Types
                          2. Select '{self.model_name}' → Cards
                          3. Update the following template(s):

                        {chr(10).join(templates_to_show)}

                        Note: Template updates apply immediately to all cards"""))
                else:
                    logger.debug(f"Card template for '{self.model_name}' is up to date")
            except AnkiConnectError as e:
                logger.debug(f"Could not check card template: {e}")

            # Check if CSS needs updating
            try:
                model_styling = self._invoke("modelStyling", modelName=self.model_name)
                current_css = " ".join(model_styling.get("css", "").split())
                expected_css_norm = " ".join(self.MODEL_CSS.split())

                if current_css != expected_css_norm:
                    logger.warning(dedent(f"""\
                        Model '{self.model_name}' CSS differs from expected

                        To update the CSS:
                          1. Open Anki → Tools → Manage Note Types
                          2. Select '{self.model_name}' → Cards
                          3. Click 'Styling' and update the CSS

                        Expected CSS:
                        {self.MODEL_CSS.strip()}"""))
                else:
                    logger.debug(f"CSS for '{self.model_name}' is up to date")
            except AnkiConnectError as e:
                logger.debug(f"Could not check model CSS: {e}")

        except AnkiConnectError as e:
            logger.debug(f"Could not check model fields: {e}")

    def add_note(self, highlight: dict, book: dict) -> Optional[int]:
        """Add an Anki note from a Readwise highlight.

        Args:
            highlight: Highlight data from Readwise
            book: Book/article data from Readwise

        Returns:
            Note ID if created, None if already exists
        """
        self.stats["highlights_processed"] += 1

        # Extract highlight data
        text = highlight.get("text", "")
        # Convert markdown to HTML for text
        text_html = markdown.markdown(text, extensions=["extra", "nl2br"])

        note_text = highlight.get("note", "")
        # Convert markdown to HTML for notes
        note_html = (
            markdown.markdown(note_text, extensions=["extra", "nl2br"])
            if note_text
            else ""
        )
        highlight_id = str(highlight.get("id", ""))
        updated = highlight.get(
            "updated_at", ""
        )  # Note: same as created_at if never updated
        highlight_url = highlight.get("url", "")
        color = highlight.get("color", "")
        is_favorite = highlight.get("is_favorite", False)
        tags = highlight.get("tags", [])

        # Extract book data
        title = book.get("title", "Unknown")
        author = book.get("author", "Unknown")
        source = book.get("source", "Unknown")
        category = book.get("category", "Unknown")
        readwise_url = book.get("readwise_url", "")

        # Format tags for Anki
        tag_list = [
            str(tag.get("name", "")).replace(" ", "_")
            for tag in tags
            if tag.get("name")
        ]
        tag_list.append("readwise")
        # Remove any empty or invalid tags
        tag_list = [t for t in tag_list if t and t.strip()]

        # Check if note already exists using highlight ID
        # We store highlight_id in the HighlightID field to track duplicates
        existing_notes = self._invoke(
            "findNotes", query=f'deck:"{self.deck_name}" HighlightID:{highlight_id}'
        )

        if existing_notes:
            # Get existing note info
            existing_note_info = self._invoke("notesInfo", notes=existing_notes)
            if existing_note_info:
                existing = existing_note_info[0]
                existing_fields = existing["fields"]
                note_id = existing["noteId"]

                # Check if any field needs updating
                needs_update = False
                update_fields = {}

                # Convert markdown to HTML for comparison
                text_html = markdown.markdown(text, extensions=["extra", "nl2br"])

                # Check each field - update if it exists in the model and value changed
                if (
                    "Text" in existing_fields
                    and existing_fields["Text"]["value"] != text_html
                ):
                    update_fields["Text"] = str(text_html)
                    needs_update = True
                if (
                    "Title" in existing_fields
                    and existing_fields["Title"]["value"] != title
                ):
                    update_fields["Title"] = str(title)
                    needs_update = True
                if (
                    "Author" in existing_fields
                    and existing_fields["Author"]["value"] != author
                ):
                    update_fields["Author"] = str(author)
                    needs_update = True
                if (
                    "Source" in existing_fields
                    and existing_fields["Source"]["value"] != source
                ):
                    update_fields["Source"] = str(source)
                    needs_update = True
                if (
                    "Category" in existing_fields
                    and existing_fields["Category"]["value"] != category
                ):
                    update_fields["Category"] = str(category)
                    needs_update = True
                # Convert markdown to HTML for notes
                note_html = (
                    markdown.markdown(note_text, extensions=["extra", "nl2br"])
                    if note_text
                    else ""
                )
                if (
                    "Note" in existing_fields
                    and existing_fields["Note"]["value"] != note_html
                ):
                    update_fields["Note"] = str(note_html)
                    needs_update = True
                if "Tags" in existing_fields and existing_fields["Tags"][
                    "value"
                ] != ", ".join(tag_list):
                    update_fields["Tags"] = ", ".join(tag_list)
                    needs_update = True
                if "UpdatedAt" in existing_fields and existing_fields["UpdatedAt"][
                    "value"
                ] != (str(updated) if updated else ""):
                    update_fields["UpdatedAt"] = str(updated) if updated else ""
                    needs_update = True
                if "HighlightURL" in existing_fields and existing_fields[
                    "HighlightURL"
                ]["value"] != (str(highlight_url) if highlight_url else ""):
                    update_fields["HighlightURL"] = (
                        str(highlight_url) if highlight_url else ""
                    )
                    needs_update = True
                if "ReadwiseURL" in existing_fields and existing_fields["ReadwiseURL"][
                    "value"
                ] != (str(readwise_url) if readwise_url else ""):
                    update_fields["ReadwiseURL"] = (
                        str(readwise_url) if readwise_url else ""
                    )
                    needs_update = True
                if "Color" in existing_fields and existing_fields["Color"]["value"] != (
                    str(color) if color else ""
                ):
                    update_fields["Color"] = str(color) if color else ""
                    needs_update = True
                if "IsFavorite" in existing_fields:
                    new_fav = "true" if is_favorite else ""
                    if existing_fields["IsFavorite"]["value"] != new_fav:
                        update_fields["IsFavorite"] = new_fav
                        needs_update = True

                if needs_update:
                    logger.debug(
                        f"Updating note for highlight {highlight_id} - fields changed: {', '.join(update_fields.keys())}"
                    )

                    # Update note fields
                    self._invoke(
                        "updateNoteFields",
                        note={"id": note_id, "fields": update_fields},
                    )

                    # Update tags
                    self._invoke("updateNoteTags", note=note_id, tags=tag_list)

                    self.stats["notes_updated"] += 1
                    return note_id
                else:
                    self.stats["notes_skipped"] += 1
            return None

        # Create the note - allow duplicates based on text, we track by HighlightID instead
        note = {
            "deckName": self.deck_name,
            "modelName": self.model_name,
            "fields": {
                "Text": str(text_html),
                "Title": str(title),
                "Author": str(author),
                "Source": str(source),
                "Category": str(category),
                "Note": str(note_html),
                "Tags": ", ".join(tag_list),
                "HighlightID": str(highlight_id),
                "UpdatedAt": str(updated) if updated else "",
                "HighlightURL": str(highlight_url) if highlight_url else "",
                "ReadwiseURL": str(readwise_url) if readwise_url else "",
                "Color": str(color) if color else "",
                "IsFavorite": "true" if is_favorite else "",
            },
            "tags": tag_list,
            "options": {
                "allowDuplicate": True,  # Allow duplicate text, we check HighlightID instead
                "duplicateScope": "deck",
            },
        }

        try:
            note_id = self._invoke("addNote", note=note)
            self.stats["notes_added"] += 1
            logger.debug(f"Added new note: {highlight_id}")
            return note_id
        except AnkiConnectError as e:
            logger.error(f"Error adding note for highlight {highlight_id}: {e}")
            return None

    def suspend_note(self, highlight_id: str) -> bool:
        """Suspend a note by highlight ID.

        Args:
            highlight_id: The Readwise highlight ID

        Returns:
            True if note was suspended, False otherwise
        """
        existing_notes = self._invoke(
            "findNotes", query=f'deck:"{self.deck_name}" HighlightID:{highlight_id}'
        )

        if not existing_notes:
            logger.debug(f"No note found for highlight {highlight_id}")
            return False

        # Get the cards for this note
        note_info = self._invoke("notesInfo", notes=existing_notes)
        if note_info and note_info[0].get("cards"):
            card_ids = note_info[0]["cards"]
            # Suspend all cards for this note
            self._invoke("suspend", cards=card_ids)
            logger.debug(
                f"Suspended {len(card_ids)} card(s) for highlight {highlight_id}"
            )
            return True

        return False

    def suspend_book_notes(self, book_id: str, book_title: str) -> int:
        """Suspend all notes from a book.

        Args:
            book_id: The Readwise book/user_book_id
            book_title: The book title for searching

        Returns:
            Number of notes suspended
        """
        # Search for notes with this book title
        # Escape quotes in the title for the query
        escaped_title = book_title.replace('"', '\\"')
        existing_notes = self._invoke(
            "findNotes", query=f'deck:"{self.deck_name}" Title:"{escaped_title}"'
        )

        if not existing_notes:
            logger.debug(f"No notes found for book: {book_title}")
            return 0

        suspended_count = 0
        notes_info = self._invoke("notesInfo", notes=existing_notes)

        for note in notes_info:
            if note.get("cards"):
                card_ids = note["cards"]
                self._invoke("suspend", cards=card_ids)
                suspended_count += 1

        logger.debug(f"Suspended {suspended_count} note(s) from book: {book_title}")
        return suspended_count

    def unsuspend_note(self, highlight_id: str) -> bool:
        """Unsuspend a note by highlight ID.

        Args:
            highlight_id: The Readwise highlight ID

        Returns:
            True if note was unsuspended, False otherwise
        """
        existing_notes = self._invoke(
            "findNotes", query=f'deck:"{self.deck_name}" HighlightID:{highlight_id}'
        )

        if not existing_notes:
            logger.debug(f"No note found for highlight {highlight_id}")
            return False

        # Get the cards for this note
        note_info = self._invoke("notesInfo", notes=existing_notes)
        if note_info and note_info[0].get("cards"):
            card_ids = note_info[0]["cards"]
            # Unsuspend all cards for this note
            self._invoke("unsuspend", cards=card_ids)
            logger.debug(
                f"Unsuspended {len(card_ids)} card(s) for highlight {highlight_id}"
            )
            return True

        return False

    def delete_notes(self, note_ids: list) -> int:
        """Delete notes by their IDs.

        Args:
            note_ids: List of note IDs to delete

        Returns:
            Number of notes deleted
        """
        if not note_ids:
            return 0

        self._invoke("deleteNotes", notes=note_ids)
        logger.debug(f"Deleted {len(note_ids)} note(s)")
        return len(note_ids)

    def handle_orphaned_notes(
        self, readwise_highlight_ids: set, show_details: bool = False, delete: bool = False
    ):
        """Detect and optionally show or delete orphaned notes.

        Orphaned notes are notes that exist in Anki but not in the current Readwise export.

        Args:
            readwise_highlight_ids: Set of all highlight IDs from Readwise export
            show_details: If True, show details about each orphaned note
            delete: If True, delete orphaned notes (implies show_details=True)
        """
        # Get all notes from the deck
        all_notes = self._invoke("findNotes", query=f'deck:"{self.deck_name}"')

        if not all_notes:
            logger.info("No existing notes in deck")
            return

        # Get detailed info about all notes
        notes_info = self._invoke("notesInfo", notes=all_notes)

        orphaned_notes = []
        for note in notes_info:
            highlight_id = note["fields"].get("HighlightID", {}).get("value", "")

            if not highlight_id:
                continue

            # Check if this highlight still exists in Readwise
            if highlight_id not in readwise_highlight_ids:
                # This note exists in Anki but not in Readwise - it's orphaned
                orphaned_notes.append(note)

        if not orphaned_notes:
            logger.info("No orphaned notes found")
            return

        orphaned_count = len(orphaned_notes)
        logger.info(
            f"Found {orphaned_count} orphaned note{'s' if orphaned_count != 1 else ''} (in Anki but not in Readwise)"
        )

        # Show details if requested or if deleting
        if show_details or delete:
            for note in orphaned_notes:
                highlight_id = note["fields"].get("HighlightID", {}).get("value", "")
                title = note["fields"].get("Title", {}).get("value", "Unknown")
                text = note["fields"].get("Text", {}).get("value", "")
                # Truncate text for display
                text_preview = (
                    text[:100] + "..." if len(text) > 100 else text
                ).replace("\n", " ")

                logger.info(f"  - {highlight_id}: {title}")
                logger.info(f"    {text_preview}")

        # Delete if requested
        if delete:
            note_ids = [note["noteId"] for note in orphaned_notes]
            self.delete_notes(note_ids)
            logger.info(f"Deleted {len(note_ids)} orphaned note{'s' if len(note_ids) != 1 else ''}")
            self.stats["notes_deleted"] = len(note_ids)

        self.stats["notes_orphaned"] = orphaned_count

    def save(self, output_path: str = None) -> None:
        """Save/sync changes (no-op for AnkiConnect, notes are already saved).

        Args:
            output_path: Ignored (kept for API compatibility)
        """
        logger.info(
            f'\nProcessed {self.stats["books_processed"]} "books" with {self.stats["highlights_processed"]} highlights'
        )
        logger.info(
            f"Added: {self.stats['notes_added']}, Updated: {self.stats['notes_updated']}, Suspended: {self.stats['notes_suspended']}, Skipped: {self.stats['notes_skipped']}"
        )
        if self.stats["books_suspended"] > 0:
            logger.info(f"Suspended books: {self.stats['books_suspended']}")
        if self.stats.get("notes_orphaned", 0) > 0:
            logger.info(f"Orphaned notes: {self.stats['notes_orphaned']}")
