import logging
import os

from dotenv import load_dotenv
from google.cloud import firestore

from models.Member import Member

load_dotenv()
logger = logging.getLogger(__name__)
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION")
class UserAPIClient:
    def __init__(self):
        self.db = firestore.Client(project='keypractica')
        # Use collection group for subcollection
        self.collection = self.db.collection_group('members')

    def check_user(self, telegram_name):
        try:
            doc = self.collection.where('telegramName', '==', telegram_name).get()
            for user in doc:
                return Member(user.get('telegramName'), user.get('vehicles'))
            return None
        except Exception as e:
            logger.error(f"Error checking user: {e}")
            return None

    def register_user(self, telegram_name):
        try:
            if not self.check_user(telegram_name):
                # Create doc reference for new user
                doc_ref = self.db.collection('kneo-store').document()
                doc_ref.set({
                    'telegramName': telegram_name,
                    'vehicles': []
                })
                return self.check_user(telegram_name)
            return None
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None