import asyncio
import os
from typing import Optional

import requests
from dotenv import load_dotenv

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
            # Debug input data
            logger.debug(f"Input file_data type: {type(file_data)}")
            logger.debug(f"Input file_data length: {len(file_data)} bytes")

            if isinstance(file_data, str):
                logger.warning("Input is string, expected bytes")
                try:
                    file_data = bytes.fromhex(file_data)
                    logger.debug("Converted hex string to bytes")
                except ValueError:
                    logger.error("Failed to convert hex string to bytes")
                    return None

            files = {
                "upload_file": ("audio.mp3", file_data, "audio/mpeg")
            }

            logger.debug("Sending request to Shazam API...")
            response = requests.post(
                self.base_url,
                headers=headers,
                files=files
            )
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response content: {response.text[:200]}...")

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