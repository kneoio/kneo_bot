import os
import requests
from datetime import datetime
from typing import Optional
import asyncio
from dotenv import load_dotenv
from models.SoundFragment import SoundFragment
from utils.logger import logger

load_dotenv()


class ShazamAPIClient:
    def __init__(self):
        self.api_key = os.getenv("SHAZAM_API_KEY")
        self.base_url = "https://shazam-api6.p.rapidapi.com/shazam/recognize/"

    async def detect_song(self, file_data: bytes) -> Optional[dict]:
        headers = {
            'x-rapidapi-host': 'shazam-api6.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        }

        try:
            files = {
                "upload_file": ("audio.mp3", file_data, "audio/mpeg")
            }
            response = requests.post(
                self.base_url,
                headers=headers,
                files=files
            )

            print(f"Response: {response.text}")

            if response.status_code == 200:
                data = response.json()
                track = data.get("track", {})
                if track:
                    metadata = {
                        "title": track.get("title"),
                        "artist": track.get("subtitle"),
                        "album": track.get("sections", [{}])[0].get("metadata", [{}])[0].get("text", "Unknown Album"),
                        "genre": track.get("genres", {}).get("primary", "Unknown"),
                        "release_date": track.get("releasedate", "Unknown"),
                        "duration": track.get("duration", 0),
                    }
                    logger.info(f"Song detected: {metadata['title']} by {metadata['artist']}")
                    return metadata
            logger.error(f"Error detecting song: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Error with Shazam API: {e}")
            return None


if __name__ == "__main__":
    file_path = "C:/Users/justa/tmp/hits_of70_80_90/013.  Camaro's  -  Companero.mp3"


    async def test():
        try:
            with open(file_path, "rb") as file:
                file_data = file.read()

            client = ShazamAPIClient()
            metadata = await client.detect_song(file_data)

            if metadata:
                print(f"Title: {metadata['title']}")
                print(f"Artist: {metadata['artist']}")
                print(f"Album: {metadata['album']}")
                print(f"Genre: {metadata['genre']}")
            else:
                print("Could not identify song")

        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error: {e}")


    asyncio.run(test())