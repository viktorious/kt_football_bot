"""
KT Football bot
©Viktor Sharov, 2024
"""

import logging
import os.path
import sys

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


def main() -> None:
    tg_bot_token_file = "tg_bot_token"
    if len(sys.argv) > 1:
        tg_bot_token_file = sys.argv[1]
    if not os.path.exists(tg_bot_token_file):
        logging.error(
            f"Unable to find {tg_bot_token_file} with Telegram bot token. Provide file name as first argument to script"
        )
        return
    with open(tg_bot_token_file) as f:
        token = f.read()
    app = ApplicationBuilder().token(token).build()
    app.run_polling()


if __name__ == "__main__":
    main()
