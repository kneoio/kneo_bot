import json
import logging
from datetime import datetime
from typing import List

from models.SoundFragment import SoundFragment
from services.SoundFragmentQueue import SoundFragmentQueue
from services.jamendo_client import JamendoAPIClient
from services.user_storage import UserStorageClient
from services.event_repository import EventRepository
from services.shazam_client import ShazamAPIClient
from services.google_tts_client import GoogleTTSClient
from services.file_processor import LocalAudioProcessor
from models.Event import Event, Precision, EventType

logger = logging.getLogger(__name__)

class ToolHandler:
    def __init__(self):
        self.sound_queue = SoundFragmentQueue()
        self.jamendo_client = JamendoAPIClient()
        self.user_client = UserStorageClient()
        self.event_repo = EventRepository()
        self.shazam_client = ShazamAPIClient()
        self.tts_client = GoogleTTSClient()
        self.audio_processor = LocalAudioProcessor()

    async def handle_check_user(self, input_data: dict) -> str:
        result = self.user_client.check_user(input_data['telegramName'])
        return json.dumps({"status": "success", "exists": bool(result)})

    async def handle_register_user(self, input_data: dict) -> str:
        result = self.user_client.register_user(input_data['telegramName'])
        return json.dumps({"status": "success" if result else "error"})

    async def handle_add_event(self, input_data: dict) -> str:
        event = Event(
            around=datetime.fromisoformat(input_data['around']),
            precision=Precision(input_data['precision']),
            description=input_data['description'],
            type=EventType(input_data['type']),
            author=input_data['author'],
            createdAt=datetime.now()
        )
        event_id = self.event_repo.add_event(event)
        return json.dumps({
            "status": "success",
            "event_id": event_id
        })

    async def handle_check_today_events(self, input_data: dict) -> str:
        events_data = self.event_repo.check_what_we_have_today()
        events = []
        for event_dict in events_data:
            try:
                events.append({
                    "description": event_dict.get('description'),
                    "around": event_dict.get('around'),
                    "precision": event_dict.get('precision'),
                    "type": event_dict.get('type'),
                    "author": event_dict.get('author'),
                    "createdAt": event_dict.get('createdAt')
                })
            except Exception as e:
                logger.error(f"Error processing event: {e}")

        return json.dumps({
            "status": "success",
            "events": events
        })

    async def handle_recognize_song(self, input_data: dict) -> str:
        try:
            audio_data = bytes.fromhex(input_data['audio_data'])
            metadata = await self.shazam_client.detect_song(audio_data)

            return json.dumps({
                "success": True,
                "metadata": metadata
            })
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return json.dumps({
                "success": False,
                "metadata": {}
            })

    async def handle_generate_audio_fragment(self, input_data: dict) -> str:
        try:
            speech_data = await self.tts_client.synthesize_speech(
                text=input_data['text'],
                voice_name=input_data.get('voice_name', 'en-US-Wavenet-D'),
                language_code=input_data.get('language_code', 'en-US')
            )

            return json.dumps({
                "success": bool(speech_data),
                "audio_data": speech_data.hex() if speech_data else ""
            })
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return json.dumps({
                "success": False,
                "audio_data": ""
            })

    async def handle_merge_audio(self, input_data: dict) -> str:
        try:
            intro_audio = bytes.fromhex(input_data['intro_audio'])
            main_audio = bytes.fromhex(input_data['main_audio'])

            merged_data = self.audio_processor.merge_audio_files(intro_audio, main_audio)

            return json.dumps({
                "success": bool(merged_data),
                "merged_audio": merged_data.hex() if merged_data else ""
            })
        except Exception as e:
            logger.error(f"Merge error: {e}")
            return json.dumps({
                "success": False,
                "merged_audio": ""
            })