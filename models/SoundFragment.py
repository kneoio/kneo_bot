import json
from dataclasses import dataclass, asdict

@dataclass
class SoundFragment:
    source: str
    file_uri: str
    type: str
    author: str
    created_at: str
    genre: str
    album: str

    def to_json(self):
        return json.dumps(asdict(self))
