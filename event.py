"""
Event description for KT Football bot
©Viktor Sharov, 2024
"""

import time

class Event:
    def __init__(self, params=None):
        time_stamp = time.time()
        cur_time = time.localtime(time_stamp - (time_stamp % 86_400) + 87_000)
        self.__event_title = ""
        self.__event_time = ""
        if params is not None:
            pass