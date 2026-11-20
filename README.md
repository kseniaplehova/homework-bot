# Homework Status Bot

A Telegram bot that polls the Yandex Practicum API and notifies you when the review status of your homework changes.

> Educational project — Yandex Practicum, Python Developer course.

## Features

- Polls the Practicum `homework_statuses` endpoint every 10 minutes (`RETRY_PERIOD = 600`), requesting changes since the last `current_date`.
- Sends a Telegram message with the homework name and a human-readable verdict for the statuses `approved`, `reviewing` and `rejected`.
- Validates the API response (type and structure checks, unknown statuses) and raises dedicated errors (`APIResponseError`, `JSONDecodeError` in `exceptions.py`) for non-200 responses, network failures and invalid JSON.
- Reports runtime failures to the same chat, without repeating an identical error message.
- Checks required environment variables on start and exits with a clear message listing the missing ones.
- Logs to stdout with timestamps.
- Includes a `Procfile` (`worker: python homework.py`) for running as a worker process on a PaaS.

## Tech stack

- Python
- pyTelegramBotAPI 4.22.1, requests 2.32.3, python-dotenv 1.0.1
- pytest 8.3.3, pytest-timeout 2.3.1, flake8 7.1.1, flake8-docstrings 1.7.0

## Getting started

```bash
git clone https://github.com/kseniaplehova/homework-bot.git
cd homework-bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set these environment variables (they can also be kept in a local dotenv file, which python-dotenv loads on start):

- `PRACTICUM_TOKEN` — Yandex Practicum API OAuth token
- `TELEGRAM_TOKEN` — Telegram bot token
- `TELEGRAM_CHAT_ID` — id of the chat to send notifications to

Then run:

```bash
python homework.py
```

## Tests

```bash
pytest
```

Tests are in `tests/` (`test_bot.py`).

## Author

Ksenia Plehova — [GitHub](https://github.com/kseniaplehova)
