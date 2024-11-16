import json
import logging
from datetime import datetime

from models.Event import Event, Precision, EventType
from models.ai_tool_result import AiToolResult
from services.audd_client import AudDAPIClient
from services.event_repository import EventRepository
from services.file_processor import LocalAudioProcessor
from services.google_tts_client import GoogleTTSClient
from services.jamendo_client import JamendoAPIClient
from services.user_storage import UserStorageClient

logger = logging.getLogger(__name__)

class ToolHandler:
    def __init__(self):
        self.jamendo_client = JamendoAPIClient()
        self.user_client = UserStorageClient()
        self.event_repo = EventRepository()
        self.shazam_client = AudDAPIClient()
        self.tts_client = GoogleTTSClient()
        self.audio_processor = LocalAudioProcessor()

    def get_handler(self, tool_name: str):
        handlers = {
            "check_user": self.handle_check_user,
            "register_user": self.handle_register_user,
            "add_event": self.handle_add_event,
            "check_today_events": self.handle_check_today_events,
            "recognize_song": self.handle_recognize_song,
            "generate_audio_fragment": self.handle_generate_audio_fragment,
            "merge_audio": self.handle_merge_audio,
        }
        return handlers.get(tool_name)

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

    async def handle_recognize_song(self, input_data: dict, context_data: dict) -> AiToolResult:
        try:
            audio_data = bytes.fromhex(context_data[input_data['message_id']])
            metadata = await self.shazam_client.detect_song(audio_data)
            return AiToolResult.from_text(f"Found: {metadata.get('title')} - {metadata.get('artist')}")
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return AiToolResult.from_exception(e)

    async def handle_generate_audio_fragment(self, input_data: dict, context_data: dict) -> AiToolResult:
        try:
            speech_data = await self.tts_client.synthesize_speech(
                text=input_data['text'],
                voice_name=input_data.get('voice_name', 'en-US-Wavenet-D'),
                language_code=input_data.get('language_code', 'en-US')
            )

            context_data['last_tts'] = speech_data
            return AiToolResult.from_audio(speech_data)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return AiToolResult.from_exception(e)

    async def handle_merge_audio(self, input_data: dict) -> AiToolResult:
        try:
            intro_audio = bytes.fromhex(input_data['intro_audio'])
            main_audio = bytes.fromhex(input_data['main_audio'])

            merged_data = self.audio_processor.merge_audio_files(intro_audio, main_audio)
            return AiToolResult.from_audio(merged_data)
        except Exception as e:
            logger.error(f"Merge error: {e}")
            return AiToolResult.from_exception(e)
