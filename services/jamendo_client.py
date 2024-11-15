import os
from typing import List

import requests
from google.cloud import storage
from dotenv import load_dotenv
from datetime import datetime
from models.SoundFragment import SoundFragment
from utils.logger import logger
from services.SoundFragmentQueue import SoundFragmentQueue

load_dotenv()


class JamendoAPIClient:
    def __init__(self):
        self.client_id = os.getenv("JAMENDO_CLIENT_ID")
        self.bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.api_base_url = "https://api.jamendo.com/v3.0"
        self.storage_client = storage.Client()

    def upload_to_gcs(self, content, blob_name):
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content)
        return f"gs://{self.bucket_name}/{blob_name}"

    def fetch_metadata_by_genre(self, genres:  List[str]):
        url = f"{self.api_base_url}/tracks"
        genre_string = "+".join(genres["genres"])
        params = {
            "client_id": self.client_id,
            "format": "json",
            "fuzzytags": genre_string,
            "limit": 1
        }

        try:
            response = requests.get(url, params=params)
            logger.info(f"Fetching metadata for genre: {genre_string}")
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    track = data["results"][0]
                    metadata = {
                        "title": track["name"],
                        "artist": track["artist_name"],
                        "album": track.get("album_name", "Unknown Album"),
                        "release_date": track["releasedate"],
                        "duration": track["duration"],
                        "genre": genre_string,
                        "stream_url": track["audio"]
                    }
                    logger.info(f"Fetched metadata for track: {metadata['title']}")
                    return metadata
                else:
                    logger.warning(f"No track found for genre: {genre_string}")
                    return None
            else:
                logger.error(f"Error fetching metadata: {response.status_code}, {response.text}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error fetching track metadata from Jamendo: {e}")
            return None

    def get_sound_fragment(self, genres:  List[str]):
        metadata = self.fetch_metadata_by_genre(genres)
        if metadata:
            response = requests.get(metadata["stream_url"], stream=True)
            response.raise_for_status()

            blob_name = f"{metadata['artist']}_{metadata['title']}.mp3"
            file_uri = self.upload_to_gcs(response.content, blob_name)

            fragment = SoundFragment(
                source="JAMENDO",
                fileUri=file_uri,
                type="SONG",
                author=metadata["artist"],
                name=metadata["title"],
                createdAt=datetime.utcnow().isoformat(),
                genre=metadata["genre"],
                album=metadata["album"]
            )
            logger.info(f"Created SoundFragment for track '{metadata['title']}' source '{fragment.source}'")
            return fragment
        else:
            logger.warning(f"Could not create SoundFragment for genre: {genres}")
            return None


if __name__ == "__main__":
    jamendo_client = JamendoAPIClient()
    sound_fragment = jamendo_client.get_sound_fragment(["house", "edm"])
    if sound_fragment:
        sound_queue = SoundFragmentQueue()
        sound_queue.publish_sound_fragment(sound_fragment)
        logger.info("SoundFragment published to Pub/Sub")
