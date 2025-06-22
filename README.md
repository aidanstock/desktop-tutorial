# Forex Telegram Bot

This repository contains a Python Telegram bot that monitors several Forex RSS feeds and sends trading alerts. It categorizes each signal using GPT-4, extracts potential TP/SL levels, and maintains an interactive dashboard on Telegram.

## Features

- Parses RSS feeds from UltreosForex, FXStreet, and DailyFX.
- Uses GPT (via the OpenAI API) to infer trend direction, signal duration, and suggested TP/SL.
- Stores the latest five signals in `cache.json`.
- Provides a /start dashboard with buttons for refreshing the feed and showing signal types.
- Automatically refreshes every 10 minutes.
- Includes a small Flask server (`keep_alive.py`) so the bot can be hosted on Replit and kept alive by UptimeRobot.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables (or edit `bot.py` to hardcode them):
   - `TELEGRAM_TOKEN` – Telegram bot token.
   - `TELEGRAM_CHAT_ID` – chat ID where alerts should be sent.
   - `OPENAI_API_KEY` – OpenAI API key for GPT-4 access.
3. Run the bot:
   ```bash
   python bot.py
   ```

The bot will start polling Telegram and checking feeds every 10 minutes.
