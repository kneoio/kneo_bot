from dotenv import load_dotenv
from google.cloud.firestore_v1.base_query import FieldFilter
from services.firebase_client import FirebaseClient
from models.Member import Member
from utils.logger import logger

load_dotenv()

class UserStorageClient:
    def __init__(self):
        self.db = FirebaseClient.get_db()

    def check_user(self, telegram_name: str) -> Member:
        try:
            docs = (
                self.db.collection("members")
                .where(filter=FieldFilter("telegramName", "==", telegram_name))
                .stream()
            )

            member = None
            for doc in docs:
                print(f"{doc.id} => {doc.to_dict()}")
                data = doc.to_dict()
                member = Member(telegram_name)
                member.__dict__.update(data)

            if not member:
                return self.register_user(telegram_name)

            return member
        except Exception as e:
            logger.error(f"Error checking user: {e}")
            return None

    def register_user(self, telegram_name: str) -> Member:
        try:
            member = Member(telegram_name)
            doc_ref = self.db.collection("members").document(telegram_name)
            doc_ref.set(member.__dict__)
            return member
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None