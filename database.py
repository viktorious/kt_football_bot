"""
SQLite database support functions for kt_football_bot bot
Creates and supports tables in database:
    - event
      Event description:
      - Title of event
      - Time of event
      - Address of event
      - Timestamp of message - timestamp when message was created in chat;
                               could be in future - in case message should be scheduled
      - Chan id - in which chat event was created
      - Limit of players - how many players takes participate in action; players beyond limit are added to queue
    - event_member
    Event participants:
      - Event id
      - user id (Telegram unique user id)
      - name (user visible name taken from Telegram)
      - username (user Telegram nick, if exists)
      - timestamps of joining to create proper sequence of joined players
      - count - how many times player clicked "join" in event message
    Note: there is no "user" table - user information is taken from Telegram
    - ban
    Banned user list
      - Chat id
      - User id
      -
"""
import aiosqlite
import logging

logger = logging.getLogger(__name__)


class FootballBotDatabase:

    SQL_CREATE_DB = [
        (
            "create table if not exists "
            "event(id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "event_title TEXT, "
            "event_time REAL, "
            "event_address TEXT, "
            "message_timestamp REAL, "
            "message_id INTEGER(8) NOT NULL, "
            "chat_id INTEGER(8) NOT NULL, "
            "players_limit INTEGER(4) DEFAULT 21)"
        ),
        (
            "create table if not exists "
             "event_member(id INTEGER PRIMARY KEY AUTOINCREMENT, "
             "event_id INTEGER NOT NULL, "
             "user_id INTEGER(8) NOT NULL, "
             "name text, "
             "username text, "
             "join_timestamp REAL,"
             "count INTEGER default 1)"
        ),
        (
            "create table if not exists "
            "ban(id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "chat_id INTEGER NOT NULL, "
            "user_id INTEGER(8) NOT NULL, "
            "end_timestamp REAL)"
        ),
        "create index if not exists event_event_time_idx on event(event_time)",
        "create index if not exists event_event_time_chat on event(chat_id)",
        "create unique index if not exists member_event_filter on event_member(event_id, user_id)",
        "create index if not exists member_event_time_order on event_member(event_id, user_id, join_timestamp)",
        "create index if not exists ban_user on ban(chat_id, user_id, join_timestamp)",
    ]

    def __init__(self, file_name="kt_football.db"):
        self.__db_file_name = file_name
        self.__db = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self.__db is None:
            self.__db = await aiosqlite.connect(self.__db_file_name)
            for sql in self.SQL_CREATE_DB:
                try:
                    logger.info(f"Execute SQL: {sql}")
                    await self.__db.execute(sql)
                except Exception as e:
                    logger.error(e)
                    logger.error(repr(e))
                    raise
        return self.__db

    async def create_event(
        self, event_title, event_time, event_address, message_time, message_id, chat_id, players_limit=21
    ):
        event_title = str(event_title).replace("'", "")
        event_title = str(event_title).replace('"', "")
        event_address = str(event_address).replace("'", "")
        event_address = str(event_address).replace('"', "")
        event_time = float(event_time)
        message_time = float(message_time)
        message_id = int(message_id)
        chat_id = int(chat_id)
        players_limit = int(players_limit)
        db: aiosqlite.Connection = await self._get_db()

        await db.execute(
            f"insert into event(event_title, event_time, event_address, message_timestamp, message_id, chat_id, players_limit) "
            f"values('{event_title}', '{event_time}', '{event_address}', '{message_time}', '{message_id}', '{chat_id}', '{players_limit}')"
        )
        cursor = await db.execute("select last_insert_rowid()")
        rows = await cursor.fetchall()
        primary_key = rows[0][0]
        await db.commit()
        return primary_key

    async def update_event(self, event_id, event_descr):
        """
        Update event description in database
        :param event_id: Event identifier in database
        :param event_descr: Dictionary of items to update. Possible update:
           'title', 'time', 'address', 'players_limit'
        """
        allowed_keys = {"title": "event_title",
                        "time": "event_time",
                        "address": "event_address",
                        "players_limit": "players_limit"}
        sql = []
        for key, db_key in allowed_keys.items():
            if key in event_descr:
                s = str(event_descr[key]).replace("'", "").replace('"', "")
                sql.append(f"{db_key}='{s}'")
        if len(sql) > 0:
            sql = f"update event set {','.join(sql)}"
            db: aiosqlite.Connection = await self._get_db()
            await db.execute(sql)

    async def get_all_events(self):
        db: aiosqlite.Connection = await self._get_db()
        async with db.execute("select * from event order by event_time") as cursor:
            rows = await cursor.fetchall()
        return rows
