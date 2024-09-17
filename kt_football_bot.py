"""
KT Football bot
©Viktor Sharov, 2024
"""

import asyncio
import logging
import os.path
import signal
import sys

import json
import time

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

current_periodic_task = None

async def regular_task():
    for i in range(0, 20):
        logger.info(f"Note: call from regular task {time.monotonic()}")
        await asyncio.sleep(5.7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hi! Please add this bot to group!")


async def test_echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_periodic_task
    if current_periodic_task is None:
        event_loop = asyncio.get_event_loop()
        current_periodic_task = event_loop.create_task(regular_task())
    logging.info(repr(update.message.chat))
    await context.bot.send_message(
        update.message.chat_id, "<b>NEW MESSAGE</b><pre>+---------------------+-----+\n"
                                "|1 | vsharov <a href=\"tg://user?id=123456789\">vsharov</a>         | 0.2 |\n"
                                "|2 | Not vsharov      | 0.3 |\n"
                                "+---------------------+-----+\n</pre>",
        parse_mode="HTML"
    )


def main() -> None:

    logging.basicConfig(filename="kt_football_bot.log", level=logging.INFO)

    credentials_file = "credentials.json"
    if len(sys.argv) > 1:
        credentials_file = sys.argv[1]
    if not os.path.exists(credentials_file):
        logging.error(
            f"Unable to find {credentials_file} with Telegram bot token. Provide file name as first argument to script"
        )
        return

    with open(credentials_file) as f:
        credentials = json.loads(f.read())
    token = credentials["tg_bot_token"]
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("echo", test_echo))
    logging.info("Run Telegram Bot webhook...")
    app.run_webhook(
        listen=credentials["web_addr"] if "web_addr" in credentials else "0.0.0.0",
        port=credentials["web_port"] if "web_addr" in credentials else 80,
        # url_path=credentials["web_path"],
        cert=credentials["cert"],
        key=credentials["key"],
        webhook_url=credentials["web_hook_url"],
        stop_signals=[signal.SIGTERM, signal.SIGINT],
        secret_token=credentials["web_hook_token"],
    )
    global current_periodic_task
    if current_periodic_task is None:
        current_periodic_task.cancel()


if __name__ == "__main__":
    main()
