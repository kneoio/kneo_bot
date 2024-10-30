import os
import requests
import base64
from dotenv import load_dotenv
from datetime import datetime
from models.SoundFragment import SoundFragment
from utils.logger import logger
from services.SoundFragmentQueue import SoundFragmentQueue

load_dotenv()

class JamendoAPIClient:
    def __init__(self):
        self.client_id = os.getenv("JAMENDO_CLIENT_ID")
        self.api_base_url = "https://api.jamendo.com/v3.0"
        if not self.client_id:
            logger.error("JAMENDO_CLIENT_ID is not set in environment variables")

    def fetch_metadata_by_genre(self, genre):
        url = f"{self.api_base_url}/tracks"
        params = {
            "client_id": self.client_id,
            "format": "json",
            "tags": genre,
            "limit": 1
        }

        try:
            response = requests.get(url, params=params)
            logger.info(f"Fetching metadata for genre: {genre}")
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
                        "genre": genre,
                        "stream_url": track["audio"]
                    }
                    logger.info(f"Fetched metadata for track: {metadata['title']}")
                    return metadata
                else:
                    logger.warning(f"No track found for genre: {genre}")
                    return None
            else:
                logger.error(f"Error fetching metadata: {response.status_code}, {response.text}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error fetching track metadata from Jamendo: {e}")
            return None

    def create_sound_fragment(self, genre):
        metadata = self.fetch_metadata_by_genre(genre)
        if metadata:
            response = requests.get(metadata["stream_url"], stream=True)
            response.raise_for_status()
            encoded_audio = base64.b64encode(response.content).decode("utf-8")
            fragment = SoundFragment(
                source="jamendo",
                file_uri=encoded_audio,
                type="song",
                author=metadata["artist"],
                created_at=datetime.utcnow().isoformat(),
                genre=metadata["genre"],
                album=metadata["album"]
            )
            logger.info(f"Created SoundFragment for track '{metadata['title']}'")
            return fragment
        else:
            logger.warning(f"Could not create SoundFragment for genre: {genre}")
            return None

# Test call to fetch, create, and publish a song to Pub/Sub
if __name__ == "__main__":
    jamendo_client = JamendoAPIClient()
    sound_fragment = jamendo_client.create_sound_fragment("synthpop")
    if sound_fragment:
        sound_queue = SoundFragmentQueue()
        sound_queue.publish_sound_fragment(sound_fragment)
        logger.info("SoundFragment published to Pub/Sub")
