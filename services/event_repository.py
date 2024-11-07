import json
from datetime import datetime

from google.cloud.firestore_v1 import FieldFilter

from models import Event
from services.firebase_client import FirebaseClient


class EventRepository:
   def __init__(self):
       self.db = FirebaseClient.get_db()

   def check_what_we_have_today(self) -> list:
       today = datetime.now().strftime("%Y-%m-%d")
       docs = self.db.collection('events').where(filter=FieldFilter("around", ">=", today)).stream()
       return [doc.to_dict() for doc in docs]  # Return raw dictionary data from Firestore

   def add_event(self, event: Event) -> str:
       doc_ref = self.db.collection('events').document()
       doc_ref.set(json.loads(event.to_json()))
       return doc_ref.id