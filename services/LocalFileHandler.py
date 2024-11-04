import os
from datetime import datetime
from google.cloud import storage
from models.SoundFragment import SoundFragment
from services.SoundFragmentQueue import SoundFragmentQueue
from utils.logger import logger


class LocalAudioProcessor:
    def __init__(self, file_path, bucket_name):
        self.file_path = file_path
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()

    def upload_to_gcs(self):
        try:
            blob_name = os.path.basename(self.file_path)
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)

            # Upload file to GCS
            blob.upload_from_filename(self.file_path)
            file_uri = f"gs://{self.bucket_name}/{blob_name}"
            logger.info(f"File uploaded to GCS with URI: {file_uri}")
            return file_uri
        except Exception as e:
            logger.error(f"Error uploading file to GCS: {e}")
            return None

    def create_sound_fragment(self, genre="Unknown Genre", author="Unknown Artist", album="Unknown Album"):
        # Upload the file to GCS and retrieve the URI
        file_uri = self.upload_to_gcs()
        if not file_uri:
            logger.error("Failed to upload file to GCS, cannot create SoundFragment")
            return None

        # Create the SoundFragment object with the URI instead of Base64-encoded file data
        fragment = SoundFragment(
            source="gcs",
            fileUri=file_uri,  # Store the URI instead of the encoded audio
            type="song",
            author=author,
            createdAt=datetime.utcnow().isoformat(),
            genre=genre,
            album=album
        )

        logger.info(f"Created SoundFragment for file with URI '{file_uri}'")
        return fragment


# Test call to create and publish a SoundFragment to Pub/Sub
if __name__ == "__main__":
    file_path = "C:/Users/justa/Music/lala.mp3"
    bucket_name = os.getenv("GCP_BUCKET_NAME")
    audio_processor = LocalAudioProcessor(file_path, bucket_name)

    # Create SoundFragment from local file
    sound_fragment = audio_processor.create_sound_fragment(genre="test", author="Sample Artist", album="Sample Album")

    # Publish the SoundFragment to Pub/Sub if it was successfully created
    if sound_fragment:
        sound_queue = SoundFragmentQueue()
        sound_queue.publish_sound_fragment(sound_fragment)
        logger.info("SoundFragment published to Pub/Sub with URI")
