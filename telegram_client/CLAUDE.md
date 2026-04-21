# Project: Telegram File Downloader (User Only)

## Goal
Build a Python app that monitors Telegram messages from ONE specific user and downloads file attachments (PDFs, docs, etc.) to a local folder.

This must use a Telegram client (user account), not a bot.

## MVP Requirements
The app should:
1. authenticate using Telegram API credentials
2. monitor messages from a configured user
3. detect file attachments
4. download files to a local directory
5. avoid duplicate downloads
6. log key actions and errors

Do NOT implement group support yet.

## Tech
- Language: Python
- Use a Telegram client library (user session, not bot API)
- Use `.env` for config

## Config (via .env)
- API_ID
- API_HASH
- TARGET_USER (username or user id)
- DOWNLOAD_DIR
- STATE_FILE (or DB path)
- LOG_LEVEL

Provide a `.env.example`.

## Structure (keep simple)
- src/
  - main.py
  - config.py
  - telegram_client.py
  - downloader.py
  - state.py
- downloads/
- data/

## Deduplication
Must persist processed message IDs (JSON or SQLite).
Never download the same file twice.

## File Handling
- Download common file types (pdf, doc, zip, etc.)
- Preserve filenames where possible
- Avoid overwriting files

## Logging
Log:
- startup
- auth success/failure
- target user resolved
- new file detected
- download success
- skipped duplicates
- errors

## Implementation Rules
- Keep code clean and modular
- Use type hints
- Prefer simple solutions over complex abstractions
- No unnecessary frameworks
- No over-engineering

## Delivery Order
1. project scaffold
2. config loading
3. Telegram auth
4. resolve target user
5. listen for messages
6. detect + download files
7. add dedupe
8. improve logging + README

## First Priority
Get a working end-to-end flow:
auth → detect message → download file → skip duplicates