# readwise2anki

CLI tool to sync Readwise highlights to Anki using AnkiConnect.

## Prerequisites

1. **Anki** - Install from [ankiweb.net](https://apps.ankiweb.net/)
2. **AnkiConnect add-on** - Install from [AnkiWeb](https://ankiweb.net/shared/info/2055492159)
   - In Anki: Tools → Add-ons → Get Add-ons
   - Enter code: `2055492159`
   - Restart Anki
   - **Keep Anki running** while syncing
3. **Readwise API Token** - Get from [readwise.io/access_token](https://readwise.io/access_token)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd readwise2anki

# Install dependencies
uv sync
```

## Usage

**Important: Make sure Anki is running before syncing!**

### Sync Highlights

```bash
# Sync from Readwise API
readwise2anki sync --api-token YOUR_TOKEN

# Or set environment variable
export READWISE_API_TOKEN=your_token
readwise2anki sync

# Specify a custom Anki deck (default: Readwise::imports)
readwise2anki sync --deck "MyDeck::MySubdeck"

# Use cached data for development
readwise2anki sync --use-cache

# Enable verbose output
readwise2anki sync --verbose

# Flags can also be placed before the subcommand
readwise2anki --verbose --use-cache sync
```

### Manage Orphaned Notes

Orphaned notes are highlights that exist in Anki but have been deleted from Readwise.

```bash
# Show orphaned notes
readwise2anki show-orphaned

# Delete orphaned notes
readwise2anki delete-orphaned

# Use with cache for development
readwise2anki show-orphaned --use-cache --verbose
```

## Configuration

### Deck Path

By default, highlights are synced to `Readwise::imports` (a subdeck under Readwise). You can customize this with the `--deck` option:

```bash
# Sync to a top-level deck
readwise2anki --deck "Readwise"

# Sync to a custom nested deck
readwise2anki --deck "Learning::Readwise::Books"
```

### Enable Auto Advance (Optional)

**Requires Anki 23.12 or later**

To automatically reveal the answer after a brief moment:

1. Open Anki
2. Click the gear icon next to your deck (e.g., "Readwise::imports")
3. Select "Options"
4. Go to the "Timer" tab
5. Set **"Seconds to show question for"** to `0.1` (must be non-zero)
6. When reviewing cards, click the **More** button (three dots)
7. Select **"Auto Advance"** to start

Auto Advance will now automatically show the answer almost immediately, making it easier to review your highlights continuously.

## Features

- Syncs highlights from Readwise to Anki
- Creates custom card template with:
  - Highlight text with source attribution
  - Author, source, category metadata
  - Personal notes from Readwise
  - Color indicators for highlighted text
  - Favorite markers (❤️) for important highlights
  - Links to original source and Readwise
- Automatic duplicate detection using highlight IDs
- Updates existing cards when highlights change in Readwise
- **Orphaned notes management**: Show and optionally delete notes that were deleted from Readwise
- Tracks sync statistics

## Development

```bash
# Run sync with cache for testing
make run-dev

# Show all available make targets
make help
```

### Available Make Targets

- `make sync` - Sync highlights to Anki
- `make show-orphaned` - Show orphaned notes
- `make delete-orphaned` - Delete orphaned notes
- `make run-dev` - Run sync with local cache
- `make show-orphaned-dev` - Show orphaned notes using local cache
- `make delete-orphaned-dev` - Delete orphaned notes using local cache