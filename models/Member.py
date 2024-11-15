from datetime import date
from typing import Dict, List

class Member:
    def __init__(self, name: str):
        self.telegramName = name
        self.realName = name
        self.nicknames: List[str] = []
        self.preferred_genres: Dict[str, float] = {
            "pop": 90,
            "idm": 60,
            "industrial": 85,
            "synthpop": 80,
            "ambient": 30
        }
        self.preferred_languages: Dict[str, float] = {}
        self.birthday: date = None
        self.located: str = ""
        self.obsessions: List[str] = []
        self.friends: Dict['Member', str] = {}