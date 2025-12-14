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

```bash
# Sync from Readwise API
readwise2anki --api-token YOUR_TOKEN

# Or set environment variable
export READWISE_API_TOKEN=your_token
readwise2anki

# Use cached data for development
readwise2anki --use-cache

# Enable verbose output
readwise2anki --verbose
```

## Configuration

### Enable Auto Advance (Optional)

**Requires Anki 23.12 or later**

To automatically reveal the answer after a brief moment:

1. Open Anki
2. Click the gear icon next to the "Readwise" deck
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
- Identifies orphaned cards (in Anki but deleted from Readwise)
- Tracks sync statistics

## Development

```bash
# Run with cache for testing
make run-dev
```