# services/firebase_client.py
import os
import logging
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()
logger = logging.getLogger(__name__)

class FirebaseClient:
   _instance = None
   _db = None

   @classmethod
   def get_instance(cls):
       if not cls._instance:
           cls._instance = cls()
           cred = credentials.Certificate("keypractica-38e051a4e5f3.json")
           firebase_admin.initialize_app(cred)
           cls._db = firestore.client()
       return cls._instance

   @classmethod
   def get_db(cls):
       if not cls._db:
           cls.get_instance()
       return cls._db