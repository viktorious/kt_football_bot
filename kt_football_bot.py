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
from datetime import datetime

from typing import Optional

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from database import FootballBotDatabase

logger = logging.getLogger(__name__)

database: Optional[FootballBotDatabase] = None

# current_periodic_task = None

# async def regular_task():
#     for i in range(0, 20):
#         logger.info(f"Note: call from regular task {time.monotonic()}")
#         await asyncio.sleep(5.7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello from KT Football Bot")


async def kt_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # await update.message.reply_text(f"...creating event...")
    event_list = await database.get_all_events()
    await update.message.reply_text(str(event_list))

    cur_time = time.time()
    # next day, 18:30
    event_time = (cur_time % 86_400) + 86400 + 66_600 # + 1 day  + 18:30
    event_time_struct = time.localtime(event_time)
    event_title = f"⚽️Футбол {event_time_struct.tm_mday}-{event_time_struct.tm_mon}-{event_time_struct.tm_mday} 18:30⚽️"
    players_limit = 21
    db_id = await database.create_event(
        event_title,
        event_time,
        cur_time,
        -1,
        update.message.chat_id,
        players_limit
    )
    msg = await context.bot.send_message(
        update.message.chat_id,
        f"<b>{event_title}</b>\n"
        f"Ліміт гравців: {players_limit}"
        "\n\n"
        "1. Viktor Sharov (the_viktorious)\n"
        f"\t\t⏱0.12 seconds\n\n"
        "2. Viktor Sharov (the_viktorious)\n"
        f"\t\t⏱0.21 seconds\n\n",
        parse_mode="HTML",
    )
    logger.info(f"Created message id is {msg.id}; record db id is {db_id}")


async def test_echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # global current_periodic_task
    # if current_periodic_task is None:
    #     event_loop = asyncio.get_event_loop()
    #     current_periodic_task = event_loop.create_task(regular_task())
    logging.info(repr(update.message.chat))

    await context.bot.send_message(
        update.message.chat_id,
        "<b>👟NEW MESSAGE👟</b>\n"
        "\n"
        "1. Viktor Sharov\n"
        f'\t<a href="tg://user?id={update.effective_user.id}">@the_viktorious</a>\n'
        f"\t⏱0.12 seconds\n\n"
        "2. Viktor Sharov\n"
        f'\t<a href="tg://user?id={update.effective_user.id}">@the_viktorious</a>\n'
        f"\t⏱0.12 seconds\n\n",
        parse_mode="HTML",
    )


def main() -> None:
    global database
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
    app.add_handler(CommandHandler("kt_add_event", kt_create_event))
    logging.info("Run Telegram Bot webhook...")
    database = FootballBotDatabase(
        credentials["db_path"] if "db_path" in credentials else "kt_football.db"
    )
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
    # global current_periodic_task
    # if current_periodic_task is None:
    #     current_periodic_task.cancel()


if __name__ == "__main__":
    main()
