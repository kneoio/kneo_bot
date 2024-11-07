import json
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict

class Precision(Enum):
    EXACT = "exact_time"
    MORNING = "morning" 
    AFTERNOON = "afternoon"
    EVENING = "evening"
    DURING_DAY = "during_day"
    ANYTIME = "anytime"

class EventType(Enum):
    BIRTHDAY = "birthday"
    ERRAND = "errand"
    REMINDER = "reminder"
    MEETING = "meeting"
    DEADLINE = "deadline"

@dataclass
class Event:
    around: datetime
    precision: Precision
    description: str
    type: EventType
    author: str
    createdAt: datetime

    def to_dict(self):
        return {
            "around": self.around.isoformat(),
            "precision": self.precision.value,
            "description": self.description,
            "type": self.type.value,
            "author": self.author,
            "createdAt": self.createdAt.isoformat()
        }

    @staticmethod
    def from_dict(data: dict):
        return Event(
            around=datetime.fromisoformat(data['around']),
            precision=Precision(data['precision']),
            description=data['description'],
            type=EventType(data['type']),
            author=data['author'],
            createdAt=datetime.fromisoformat(data['createdAt'])
        )