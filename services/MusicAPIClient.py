import json
import os
import logging
import requests
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class Track:
    title: str
    artist: str
    url: str
    duration: int = 0
    added_by: str = ""

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "url": self.url,
            "duration": self.duration,
            "added_by": self.added_by
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Track':
        return Track(
            title=data.get('title', ''),
            artist=data.get('artist', ''),
            url=data.get('url', ''),
            duration=data.get('duration', 0),
            added_by=data.get('added_by', '')
        )


class MusicAPIClient:
    def __init__(self):
        self.jwt_token = os.getenv('JWT_TOKEN')
        self.api_base_url = os.getenv('API_BASE_URL')
        self.app_name = os.getenv('APP_NAME')
        self.headers = {
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str, payload: Dict = None) -> Optional[Dict]:
        """Make HTTP request to the API with error handling"""
        try:
            url = f"{self.api_base_url}/api/{self.app_name}/music/{endpoint}"
            logger.info(f"Making {method} request to: {url}")
            if payload:
                logger.info(f"Request payload: {json.dumps(payload, indent=2)}")

            response = requests.request(method, url, headers=self.headers, json=payload)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response content: {response.text}")

            if response.status_code in (200, 201):
                return response.json()
            else:
                logger.error(f"Error: {response.status_code}, Response: {response.text}")
                return None

        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            return None

    def get_queue(self, chat_id: str) -> List[Track]:
        """Get the current music queue for a chat"""
        response = self._make_request('GET', f'queue/{chat_id}')
        if response and 'payload' in response:
            return [Track.from_dict(track) for track in response['payload'].get('queue', [])]
        return []

    def add_to_queue(self, chat_id: str, track: Track) -> Optional[Dict]:
        """Add a track to the queue"""
        payload = {
            "chatId": chat_id,
            "track": track.to_dict()
        }
        return self._make_request('POST', 'queue/add', payload)

    def remove_from_queue(self, chat_id: str, track_index: int) -> Optional[Dict]:
        """Remove a track from the queue by index"""
        payload = {
            "chatId": chat_id,
            "index": track_index
        }
        return self._make_request('DELETE', 'queue/remove', payload)

    def clear_queue(self, chat_id: str) -> Optional[Dict]:
        """Clear the entire queue for a chat"""
        return self._make_request('DELETE', f'queue/{chat_id}')

    def skip_current(self, chat_id: str) -> Optional[Dict]:
        """Skip the currently playing track"""
        return self._make_request('POST', f'player/{chat_id}/skip')

    def pause(self, chat_id: str) -> Optional[Dict]:
        """Pause the current playback"""
        return self._make_request('POST', f'player/{chat_id}/pause')

    def resume(self, chat_id: str) -> Optional[Dict]:
        """Resume the current playback"""
        return self._make_request('POST', f'player/{chat_id}/resume')

    def get_current_track(self, chat_id: str) -> Optional[Track]:
        """Get information about the currently playing track"""
        response = self._make_request('GET', f'player/{chat_id}/current')
        if response and 'payload' in response and 'currentTrack' in response['payload']:
            return Track.from_dict(response['payload']['currentTrack'])
        return None

    def save_favorite(self, user_id: str, track: Track) -> Optional[Dict]:
        """Save a track to user's favorites"""
        payload = {
            "userId": user_id,
            "track": track.to_dict()
        }
        return self._make_request('POST', 'favorites/add', payload)

    def get_favorites(self, user_id: str) -> List[Track]:
        """Get user's favorite tracks"""
        response = self._make_request('GET', f'favorites/{user_id}')
        if response and 'payload' in response:
            return [Track.from_dict(track) for track in response['payload'].get('favorites', [])]
        return []

    def remove_favorite(self, user_id: str, track_id: str) -> Optional[Dict]:
        """Remove a track from user's favorites"""
        payload = {
            "userId": user_id,
            "trackId": track_id
        }
        return self._make_request('DELETE', 'favorites/remove', payload)

    def get_player_status(self, chat_id: str) -> Dict:
        """Get the current status of the music player"""
        response = self._make_request('GET', f'player/{chat_id}/status')
        if response and 'payload' in response:
            return response['payload']
        return {
            'isPlaying': False,
            'currentTrack': None,
            'queueLength': 0,
            'volume': 0
        }


# Example usage
if __name__ == "__main__":
    # Initialize the client
    music_client = MusicAPIClient()

    # Example track
    track = Track(
        title="Example Song",
        artist="Example Artist",
        url="https://example.com/song.mp3",
        duration=180,
        added_by="user123"
    )

    # Example chat ID
    chat_id = "example_chat_123"

    # Add track to queue
    result = music_client.add_to_queue(chat_id, track)
    if result:
        print("Track added to queue")

    # Get current queue
    queue = music_client.get_queue(chat_id)
    for i, track in enumerate(queue):
        print(f"{i + 1}. {track.title} by {track.artist}")

    # Get player status
    status = music_client.get_player_status(chat_id)
    print(f"Player status: {'Playing' if status['isPlaying'] else 'Paused'}")