from google.cloud import pubsub_v1
from dotenv import load_dotenv

from models import SoundFragment
from utils.logger import logger
import os

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
PUBSUB_TOPIC_NAME = os.getenv("PUBSUB_TOPIC_NAME")


class SoundFragmentQueue:
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(GCP_PROJECT_ID, PUBSUB_TOPIC_NAME)
        logger.info(f"Initialized SoundFragmentQueue for project: {GCP_PROJECT_ID}, topic: {PUBSUB_TOPIC_NAME}")

    def publish_sound_fragment(self, fragment: SoundFragment):
        message_json = fragment.to_json()
        future = self.publisher.publish(self.topic_path, data=message_json.encode("utf-8"))
        logger.info(f"Published SoundFragment with message ID: {future.result()}")
