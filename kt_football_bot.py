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

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

import event as bot_event
import database as bot_db

logger = logging.getLogger(__name__)

current_periodic_task = None
current_periodic_task_stopped = False
current_periodic_task_queue = []


async def regular_task():
    global current_periodic_task_queue
    while not current_periodic_task_stopped:
        if len(current_periodic_task_queue) == 0:
            time.sleep(2)
            continue
        queue = current_periodic_task_queue[:]
        current_periodic_task_queue.clear()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello from KT Football Bot")


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """Build menu from buttons for telegram message"""
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu

async def kt_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # check if event with same address and same time already created
    chat_id = update.message.chat_id
    new_event = bot_event.Event(update.message.text)
    logger.info(f"NOTE: message text is {update.message.text}")
    event_list = await bot_event.Event.event_list(chat_id=chat_id)
    for event in event_list:
        if str(new_event.address).lower() == str(event.address).lower():
            new_time = time.mktime(new_event.time.timetuple())
            existing_time = time.mktime(event.time.timetuple())
            if abs(new_time - existing_time) < 3600:
                await update.message.reply_text(f"На цей час вже є запланована гра: {event.address} {event.time}",
                                                parse_mode="HTML")
                return
    # store new event in database and create event message
    new_event.store_to_db(update.message.chat_id)

    button_list = [
        InlineKeyboardButton("Так", callback_data='ADD'),
        InlineKeyboardButton("Ні", callback_data='REMOVE'),
    ]
    markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))

    msg = await context.bot.send_message(
        update.message.chat_id,
        new_event.create_html_message(update.message.chat_id),
        parse_mode="HTML",
        reply_markup=markup
    )
    new_event.update_message_id(msg.id)

async def button(update, context):
    """Process clicking buttons for EVENT (register/unregister player)"""
    chat_id = update.effective_message.chat_id
    data = update.callback_query.data
    await context.bot.send_message(chat_id, f"Pressed: {data} in {chat_id}")
    await update.callback_query.answer()


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
    app.add_handler(CommandHandler("kt_add_event", kt_create_event))
    app.add_handler(CallbackQueryHandler(button))
    logging.info("Run Telegram Bot webhook...")

    # init database
    bot_db.FootballBotDatabase.instance(credentials["db_path"] if "db_path" in credentials else "kt_football.db")

    # run background task for updating messages
    global current_periodic_task
    if current_periodic_task is None:
        event_loop = asyncio.get_event_loop()
        current_periodic_task = event_loop.create_task(regular_task())

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
