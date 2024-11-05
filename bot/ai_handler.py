import json
import logging
import os
from typing import List

import anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

from bot.constants import UNDEFINED
from models.SoundFragment import SoundFragment
from services.MusicAPIClient import MusicAPIClient, Track
from services.SoundFragmentQueue import SoundFragmentQueue
from services.UserAPIClient import UserAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TOPIC_NAME = os.getenv("PUBSUB_TOPIC_NAME")


def load_tool_definitions():
    try:
        with open('tools_definition/base_tools.json', 'r') as file:
            data = json.load(file)
            return data['tools']
    except Exception as e:
        logger.error(f"Error loading tool definitions: {e}")
        return []


class AIHandler:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.user_client = UserAPIClient()
        self.music_client = MusicAPIClient()
        self.tools = load_tool_definitions()

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        message_text = update.message.text

        messages = [
            {
                "role": "system",
                "content": """You are a helpful assistant that manages music queues and user interactions. 
                You can add songs to the queue and help users manage their music preferences. 
                Be conversational and friendly while helping users with their music-related requests.
                Remember the context of conversations and refer to previous interactions when relevant."""
            },
            {"role": "user", "content": message_text}
        ]

        response = await self.handle_conversation(chat_id, user_id, username, messages)
        await update.message.reply_text(response if response != UNDEFINED else "I'm not sure how to help with that.")

    async def handle_conversation(self, chat_id: str, user_id: str, username: str, messages: list) -> str:
        while True:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=messages,
                tools=self.tools
            )

            if response.stop_reason == "tool_use":
                tool_use = response.content[-1]
                tool_name = tool_use.name
                tool_input = tool_use.input

                logger.info(f"Tool use: {tool_name}")
                logger.info(f"Tool input: {tool_input}")

                tool_result = await self.process_tool_call(tool_name, tool_input, chat_id, user_id, username)

                logger.info(f"Tool result: {tool_result}")

                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(tool_result)
                    }]
                })
            else:
                return response.content[0].text

    async def process_tool_call(self, tool_name: str, tool_input: dict, chat_id: str, user_id: str,
                                username: str) -> str:
        try:
            if tool_name == "check_user":
                result = self.user_client.check_user(tool_input['telegramName'])
                return json.dumps({"status": "success", "exists": bool(result)})

            elif tool_name == "register_user":
                result = self.user_client.register_user(tool_input['telegramName'])
                return json.dumps({"status": "success" if result else "error"})

            elif tool_name == "add_to_music_queue":
                track = Track(
                    title=tool_input['title'],
                    artist=tool_input['artist'],
                    url=tool_input['url'],
                    added_by=tool_input['added_by']
                )
                result = self.music_client.add_to_queue(tool_input['chat_id'], track)
                return json.dumps({
                    "status": "success" if result else "error",
                    "message": "Track added to queue" if result else "Failed to add track"
                })
            elif tool_name == "publish_sound_fragment":
                fragment = SoundFragment(
                    source=tool_input["source"],
                    file=tool_input["file"],
                    type=tool_input["type"],
                    author=tool_input["author"],
                    createdAt=tool_input["created_at"]
                )
                logging.basicConfig(level=logging.INFO)

                sound_queue = SoundFragmentQueue(PROJECT_ID, TOPIC_NAME)
                sound_queue.publish_sound_fragment(fragment)
                return json.dumps({"status": "success", "message": "Sound fragment published to queue"})

            elif tool_name == "get_music_queue":
                queue = self.music_client.get_queue(tool_input['chat_id'])
                return json.dumps({
                    "status": "success",
                    "queue": [track.to_dict() for track in queue]
                })

            elif tool_name == "save_favorite":
                track = Track(
                    title=tool_input['title'],
                    artist=tool_input['artist'],
                    url=tool_input['url'],
                    added_by=tool_input['user_id']
                )
                result = self.music_client.save_favorite(tool_input['user_id'], track)
                return json.dumps({
                    "status": "success" if result else "error",
                    "message": "Track saved to favorites" if result else "Failed to save track"
                })

            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown tool: {tool_name}"
                })

        except Exception as e:
            logger.error(f"Error processing tool call: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def format_queue_message(self, queue: List[Track]) -> str:
        if not queue:
            return "The queue is empty"

        message = "Current queue:\n"
        for i, track in enumerate(queue, 1):
            message += f"{i}. {track.title} by {track.artist} (added by {track.added_by})\n"
        return message
