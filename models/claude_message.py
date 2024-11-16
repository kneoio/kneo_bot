from typing import List, Dict, Union, Optional
from dataclasses import dataclass

@dataclass
class ContentItem:
   type: str = "text"
   text: str = ""

@dataclass
class ClaudeMessage:
   role: str
   content: List[ContentItem]

   @classmethod
   def user_message(cls, text: str) -> "ClaudeMessage":
       return cls(
           role="user",
           content=[ContentItem(text=text)]
       )

   def to_dict(self) -> Dict:
       return {
           "role": self.role,
           "content": [{"type": item.type, "text": item.text} for item in self.content]
       }