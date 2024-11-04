import json
from dataclasses import dataclass, asdict

@dataclass
class SoundFragment:
    source: str
    fileUri: str
    name: str
    type: str
    author: str
    createdAt: str
    genre: str
    album: str

    def to_json(self):
        return json.dumps(asdict(self))
