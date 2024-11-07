import logging

from dotenv import load_dotenv
from google.cloud.firestore_v1.base_query import FieldFilter

from services.firebase_client import FirebaseClient

load_dotenv()
logger = logging.getLogger(__name__)

class UserStorageClient:
    def __init__(self):
        self.db = FirebaseClient.get_db()

    def check_user(self, telegram_name):
        global real_name
        try:
            docs = (
                self.db.collection("members")
                .where(filter=FieldFilter("telegramName", "==", telegram_name))
                .stream()
            )
            for doc in docs:
                print(f"{doc.id} => {doc.to_dict()}")
                real_name = doc.to_dict().get('realName')

            return real_name
        except Exception as e:
            logger.error(f"Error checking user: {e}")
            return None

    def register_user(self, telegram_name):
        try:
            if not self.check_user(telegram_name):
                doc_ref = self.db.collection("members").document(telegram_name)
                doc_ref.set({
                    'telegramName': telegram_name,
                    'realName': 'test'
                })
                return self.check_user(telegram_name)
            return None
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None
