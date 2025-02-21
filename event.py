"""
Event description for KT Football bot
©Viktor Sharov, 2024
"""

import datetime
import re
import time
from time import strftime
from dataclasses import dataclass

from database import FootballBotDatabase

@dataclass
class Event:
    """
    Event description with methods to create/update/delete event in database
    """
    title : str
    time : datetime.datetime
    address : str = ""
    players_limit : int = 21

    def __init__(self, message_text: str, db_id: int = None):
        self.__title = ""
        self.__time = datetime.datetime.now()
        self.__players_limit = 21
        self.__address = ""
        self.__db_id = db_id
        self.update_param(message_text, fill_default=db_id is None)

    def update_param(self, message_text: str, fill_default: bool = False):
        """
        Update event description.
        :param message_text:
        :param fill_default: True in case of need to fill event fields by pre-coded default values,
            False for update from message only
        """
        if fill_default:
            # fill default parameters for event
            # local date time
            event_date_time =  datetime.datetime.today() + datetime.timedelta(days=1)
            event_date_time = datetime.datetime(year=event_date_time.year, month=event_date_time.month,
                                                day=event_date_time.day, hour=19, minute=0, second=0)
            self.__time = event_date_time
            self.__title = (f"⚽️Футбол {event_date_time.day}-{event_date_time.month}-{event_date_time.year} "
                           f"{event_date_time.hour}:{event_date_time.minute}⚽️")
            self.__address = "🏟 Футбольне поле, вул. Липи, 6-А"
            self.__players_limit = 21
            #TODO: use per-channel default templates
        for long_line in message_text.splitlines():
            for line in long_line.split(";"):
                reg_res = re.search(r"(\w+)[=:](.+)", line)
                if reg_res is not None:
                    name = reg_res.group(1)
                    value = reg_res.group(2)
                    self.__update(name, value)

    def load_from_db(self, db_id):
        """
        Load event from database by id
        :param db_id: Primary key of event in database
        """
        pass

    def store_to_db(self, chat_id: int):
        """
        Store event to database - either create new record or update existing
        """
        self.__db_id = FootballBotDatabase.instance().create_event(
            event_title=self.__title,
            event_time=time.mktime(self.__time.timetuple()),
            event_address=self.__address,
            message_time=time.time(),
            message_id=9,
            chat_id=chat_id,
            players_limit=self.__players_limit,
        )

    def remove_from_db(self):
        """
        Remove this event from database
        """
        pass

    def create_html_message(self, chat_id):
        time_hint = strftime("%A %Y-%B-%d %H:%M", self.__time)
        html = f"<b>{self.title}</b>\n{time_hint}\n{self.address}\nКількість гравців: {self.players_limit}\n\n"
        # load participants list
        player_list = self.get_participants_list(chat_id)
        #TODO: ban list here!
        counter = 1
        for player in players_list:
            player_login = f" ({player.login})" if str(player.login) != "" else ""
            html = html + f"{counter}. {player.name}{player_login}\n\t\t{time_reaction} сек ({player.hit_count})"
            counter = counter + 1
            if int(counter) == int(self.players_limit):
                html = html + "\n\nЧерга: \n\n"
            # "1. Viktor Sharov (the_viktorious)\n"
            # f"\t\t⏱0.12 seconds\n"
            # "2. Viktor Sharov (the_viktorious)\n"
            # f"\t\t⏱0.21 seconds\n",
        return html

    @staticmethod
    async def event_list(chat_id: int) -> list["Event"]:
        db_event_list =  await FootballBotDatabase.instance().get_all_events(chat_id=chat_id)
        result = []
        for row in db_event_list:
            # id, event_title, event_time, event_address, message_timestamp, message_id, chat_id, players_limit
            item = Event(message_text="", db_id=int(row[0]))
            item.__title = str(row[1])
            item.__time = datetime.datetime.fromtimestamp(int(row[2]))
            item.__address = str(row[3])
            item.__players_limit = int(row[7])
            result.append(item)
        return result

    @dataclass
    class Player:
        """
        Player record in this particular event
        """
        # telegram name for user in event
        name: str
        # telegram login (if set) of user in event
        login: str
        # state of user: "yes", "no", "ban"
        state: str
        # when joined to event
        join_time: datetime.datetime
        # how many times pressed "join" button
        count: int = 0

    async def get_participants_list(self, chat_id):
        player_list = []
        if self.__db_id is not None:
            db_list =  await FootballBotDatabase.instance().get_member_list(self.__db_id)
        return db_list
        # return player_list

    def __update(self, name: str, value: str):
        name = name.lower()
        if name == "date" or name == "день" or name == "time" or name == "час" or name == "время":
            self.__update_date_time(value)
        if name == "title" or name == "опис" or name == "описание" or name == "заголовок":
            self.__title = value
        if name == "address" or name == "адрес" or name == "адреса":
            self.__address = value
        if name == "players_limit" or name == "limit" or name == "количество" or name == "кількість":
            try:
                self.__players_limit = int(value)
            except ValueError:
                pass

    def __update_date_time(self, value):
        # date is dd-mm-yyyy; time is hh:mm
        # possible variants: "today", "tomorrow"

        reg_res = re.search(r"\+(\d+)\s+(\w+)", value)
        if reg_res is not None:
            # parse items like "+1 hour"
            delta = None
            step = int(reg_res.group(1))
            hint = reg_res.group(2)
            if hint.startswith("min") or hint.startswith("хв") or hint.startswith("мин"):
                delta = datetime.timedelta(minutes=step)
            if hint.startswith("hour") or hint.startswith("год") or hint.startswith("час"):
                delta = datetime.timedelta(hours=step)
            if hint.startswith("day") or hint.startswith("дн") or hint.startswith("ден"):
                delta = datetime.timedelta(days=step)
            if delta is not None:
                self.__time = self.__time + delta

        year = self.__time.year
        month = self.__time.month
        day = self.__time.day
        hour = self.__time.hour
        minute = self.__time.minute

        #exact date/time in format
        reg_res = re.search(r"(\d{1,2})-(\d{1,2})-(\d{2,4})", value)
        if reg_res is not None:
            year = int(reg_res.group(3))
            month = int(reg_res.group(2))
            day = int(reg_res.group(1))
            if year < 100:
                year = 2000 + year
        reg_res = re.search(r"(\d{1,2}):(\d{1,2})", value)
        if reg_res is not None:
            hour = int(reg_res.group(1))
            minute = int(reg_res.group(2))

        today_list = ["today", "сегодня", "сьогодні"]
        tomorrow_list = ["tomorrow", "завтра"]
        add_day = 0
        for hint_list in [today_list, tomorrow_list]:
            for hint in hint_list:
                if value.find(hint) >= 0:
                    t = datetime.datetime.today()
                    if add_day >= 0:
                        t = t + datetime.timedelta(days=1)
                    year = t.year
                    month = t.month
                    day = t.day
            add_day = 1

        self.__time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=0)
