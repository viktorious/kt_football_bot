"""
SQLite database support functions for kt_football_bot bot
"""
import aiosqlite
import logging

logger = logging.getLogger(__name__)


class FootballBotDatabase:

    def __init__(self, file_name="kt_football.db"):
        self.__db_file_name = file_name
        self.__db = None
    async def _get_db(self) -> aiosqlite.Connection:
        if self.__db is None:
            self.__db = await aiosqlite.connect(self.__db_file_name)
            await self.__db.execute("create table if not exists event(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                                    "event_title TEXT, "
                                    "event_time REAL, "
                                    "message_time REAL, "
                                    "message_id INTEGER(8) NOT NULL, "
                                    "chat_id INTEGER(8) NOT NULL)")
            await self.__db.execute("create table if not exists event_member(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                                    "event_id INTEGER NOT NULL, "
                                    "user_id INTEGER(8) NOT NULL, "
                                    "name text, "
                                    "username text, "
                                    "join_time REAL)")
        return self.__db

    async def create_event(self, event_title, event_time, message_time, message_id, chat_id):
        db: aiosqlite.Connection = await self._get_db()
        event_title = str(event_title).replace("'", "")
        event_title = str(event_title).replace('"', "")
        event_time = float(event_time)
        message_time = float(message_time)
        message_id = int(message_id)
        chat_id = int(chat_id)
        await db.execute(f"insert into event(event_title, event_time, message_time, message_id, chat_id) "
                         f"values('{event_title}', '{event_time}', '{message_time}', '{message_id}', '{chat_id}')")
        cursor = await db.execute("select last_insert_rowid()")
        rows = await cursor.fetchall()
        logger.info(repr(rows))
        await db.commit()

