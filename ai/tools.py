import json
import logging
from datetime import datetime
from services.user_storage import UserStorageClient
from services.event_repository import EventRepository
from models.Event import Event, Precision, EventType

logger = logging.getLogger(__name__)


class ToolHandler:
    def __init__(self):
        self.user_client = UserStorageClient()
        self.event_repo = EventRepository()

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