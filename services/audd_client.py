import asyncio
import os
from typing import Optional
import requests
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

class AudDAPIClient:
    def __init__(self):
        self.api_token = os.getenv("AUDD_API_TOKEN")
        self.base_url = "https://api.audd.io/"

    async def detect_song(self, file_data: bytes) -> Optional[dict]:
        try:
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

            data = {
                'api_token': self.api_token,
                'return': 'spotify,apple_music,deezer'  # Optional music services
            }

            files = {
                'file': ('audio.mp3', file_data, 'audio/mpeg')
            }

            logger.debug("Sending request to AudD API...")
            response = requests.post(
                self.base_url,
                data=data,
                files=files
            )
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text[:200]}...")

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' and result.get('result'):
                    return {
                        'title': result['result']['title'],
                        'artist': result['result']['artist'],
                        'album': result['result'].get('album', ''),
                        'release_date': result['result'].get('release_date', ''),
                        'spotify': result['result'].get('spotify', {}),
                        'apple_music': result['result'].get('apple_music', {}),
                        'deezer': result['result'].get('deezer', {})
                    }
            return None

        except Exception as e:
            logger.error(f"Error with AudD API: {e}")
            return None

if __name__ == "__main__":
    file_path = "C:/Users/justa/tmp/hits_of70_80_90/013.  Camaro's  -  Companero.mp3"

    async def test():
        try:
            with open(file_path, "rb") as file:
                file_data = file.read()

            client = AudDAPIClient()
            metadata = await client.detect_song(file_data)

            if metadata:
                print(f"Title: {metadata['title']}")
                print(f"Artist: {metadata['artist']}")
                print(f"Album: {metadata['album']}")
                print(f"Release Date: {metadata['release_date']}")
                if metadata['spotify']:
                    print(f"Spotify Link: {metadata['spotify']['external_urls']['spotify']}")
            else:
                print("Could not identify song")

        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(test())