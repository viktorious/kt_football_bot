"""
KT Football bot
©Viktor Sharov, 2024
"""

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

def main() -> None:
    app = ApplicationBuilder().token("YOUR TOKEN HERE").build()
    app.run_polling()

if __name__ == "__main__":
    main()