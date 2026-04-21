# Telegram File Downloader

Monitors Telegram messages from a specific user and downloads file attachments locally.

Uses a **user account** (not a bot) via [Telethon](https://docs.telethon.dev/).

## Setup

### 1. Get Telegram API credentials
Go to https://my.telegram.org → API development tools → create an app.
Copy your `api_id` and `api_hash`.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env with your credentials
```

| Variable | Description |
|---|---|
| `API_ID` | From my.telegram.org |
| `API_HASH` | From my.telegram.org |
| `TARGET_USER` | Username (e.g. `@someone`) or numeric user ID |
| `DOWNLOAD_DIR` | Where to save files (default: `./downloads`) |
| `STATE_FILE` | Path for dedup state (default: `./data/state.json`) |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING` (default: `INFO`) |

### 4. Run
```bash
cd src
python main.py
```

On first run, Telethon will prompt for your phone number and a login code to create a session. The session is saved as `tg_session.session` so you only log in once.

## How it works

1. Authenticates as your Telegram user account
2. Resolves the target user from `TARGET_USER`
3. Listens for new messages from that user
4. When a message contains a document/file, downloads it to `DOWNLOAD_DIR`
5. Records the message ID in `STATE_FILE` to avoid re-downloading

## Notes
- Supported extensions are defined in `src/config.py` (`ALLOWED_EXTENSIONS`)
- Files are never overwritten — a counter suffix is added if a name collision occurs
- Session file (`tg_session.session`) contains your auth token; keep it private
