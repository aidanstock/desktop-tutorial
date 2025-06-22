import json
import os
import threading
import time
from datetime import datetime

import feedparser
import openai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, Updater

from keep_alive import keep_alive

TOKEN = os.getenv('TELEGRAM_TOKEN', '7919409846:AAGvy8Z5Lc4KWz9O5gNjFMBw0qgS7hHHquk')
CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID', '6707592647'))
openai.api_key = os.getenv('OPENAI_API_KEY')

FEEDS = [
    "https://blog.ultreosforex.com/feed/",
    "https://www.fxstreet.com/rss/news",
    "https://www.dailyfx.com/feeds/market-news"
]

CACHE_FILE = 'cache.json'
MAX_SIGNALS = 5

# Load cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
else:
    cache = []

cache_lock = threading.Lock()


def save_cache():
    with cache_lock:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)


def analyze_signal(text: str) -> dict:
    """Use GPT to extract TP/SL and categorize the signal."""
    if not openai.api_key:
        return {
            "category": "Unknown",
            "trend": "Unknown",
            "tp": "N/A",
            "sl": "N/A"
        }
    prompt = (
        f"Analyze the following Forex signal text and return a JSON "
        f"with keys category (Long-term/Short-term), trend (Bullish/Bearish), tp (take profit) "
        f"and sl (stop loss). Text:\n{text}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        content = response.choices[0].message['content']
        data = json.loads(content)
        return data
    except Exception as e:
        print("OpenAI error", e)
        return {
            "category": "Unknown",
            "trend": "Unknown",
            "tp": "N/A",
            "sl": "N/A"
        }


def fetch_feeds() -> list:
    new_signals = []
    for url in FEEDS:
        d = feedparser.parse(url)
        for entry in d.entries:
            link = entry.get('link')
            if any(sig['link'] == link for sig in cache):
                continue
            summary = entry.get('summary', '')
            analysis = analyze_signal(summary)
            signal = {
                'title': entry.get('title'),
                'link': link,
                'summary': summary,
                'published': entry.get('published'),
                'analysis': analysis
            }
            new_signals.append(signal)
    return new_signals


def update_signals(context: CallbackContext):
    new = fetch_feeds()
    if not new:
        return
    with cache_lock:
        cache[:0] = new  # prepend
        del cache[MAX_SIGNALS:]
    save_cache()
    for sig in new:
        text = f"{sig['title']}\n{sig['link']}\n{sig['analysis']}"
        context.bot.send_message(chat_id=CHAT_ID, text=text)


def dashboard(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("\ud83d\udcca Refresh Dashboard", callback_data='refresh')],
        [InlineKeyboardButton("\ud83d\udd0d Show Signal Types", callback_data='types')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Forex Dashboard', reply_markup=reply_markup)


def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'refresh':
        msgs = []
        with cache_lock:
            for sig in cache:
                msgs.append(f"{sig['title']} - {sig['analysis']['trend']} {sig['analysis']['category']}")
        query.edit_message_text('\n'.join(msgs))
    elif query.data == 'types':
        query.edit_message_text('Signals labeled as Long-term/Short-term and Bullish/Bearish.')


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', dashboard))
    dp.add_handler(CommandHandler('refresh', lambda u, c: update_signals(c)))
    dp.add_handler(CommandHandler('types', lambda u, c: u.message.reply_text('Signals labeled as Long-term/Short-term and Bullish/Bearish.')))
    dp.add_handler(telegram.ext.CallbackQueryHandler(button_handler))

    job = updater.job_queue
    job.run_repeating(update_signals, interval=600, first=0)

    keep_alive()
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
