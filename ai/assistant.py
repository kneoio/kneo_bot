import io
import json
import os

import anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

from ai.prompts.main_prompt import MAIN_PROMPT
from ai.tool_handler import ToolHandler
from models.ai_tool_result import AiToolResult
from models.claude_message import ClaudeMessage
from utils.logger import logger

load_dotenv()


def load_tool_definitions():
    tools = []
    base_path = 'ai/tools_definition'
    categories = ['audio']  # , 'users', 'events']

    try:
        for category in categories:
            category_path = os.path.join(base_path, category)
            if not os.path.exists(category_path):
                logger.warning(f"Category path not found: {category_path}")
                continue

            for filename in os.listdir(category_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(category_path, filename)
                    logger.debug(f"Loading tool from: {file_path}")
                    with open(file_path, 'r') as file:
                        tool = json.load(file)
                        tools.append(tool)

        logger.info(f"Loaded tools: {[t['name'] for t in tools]}")
        return tools
    except Exception as e:
        logger.error(f"Error loading tool definitions: {e}", exc_info=True)
        return []


class Assistant:
    def __init__(self):
        logger.info("Initializing Assistant...")
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.info("Loading tool definitions...")
        self.tools = load_tool_definitions()
        # logger.debug(f"Loaded tools configuration: {json.dumps(self.tools, indent=2)}")
        self.tool_handler = ToolHandler()
        logger.info("Assistant initialization completed")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if update.message.audio:
                file_obj = await context.bot.get_file(update.message.audio.file_id)
                file_data = await file_obj.download_as_bytearray()
                message_id = str(update.message.message_id)
                context.user_data[message_id] = file_data.hex()
                shared_prompt = f"An audio file has been uploaded (message_id: {message_id}). "
                if update.message.caption:
                    message_text = f"{shared_prompt}{update.message.caption}"
                else:
                    message_text = f"{shared_prompt}Recognize this song"
            else:
                message_text = update.message.text

            logger.debug(f"Prepared message text: {message_text}")

            message = ClaudeMessage.user_message(message_text)
            response = await self.handle_conversation([message.to_dict()], context)

            if response:
                await update.message.reply_text(response.get_telegram_answer())

        except Exception as e:
            logger.error(f"Error in handle_text: {e}", exc_info=True)
            await update.message.reply_text("An error occurred")

    async def handle_conversation(self, messages: list, context: ContextTypes.DEFAULT_TYPE) -> AiToolResult:
        try:
            logger.info(f"Sending request to Claude with {len(messages)} messages")

            response = self.client.messages.create(
                model=os.getenv("AI_MODEL"),
                max_tokens=1024,
                system=MAIN_PROMPT,
                messages=messages,
                tools=self.tools
            )

            if response.stop_reason == "tool_use":
                tool_use = response.content[-1]
                tool_name = tool_use.name
                tool_input = tool_use.input
                logger.info(f"Tool requested: {tool_name}")

                tool_result = await self.process_tool_call(tool_name, tool_input, context)
                logger.info(f"Tool result: {tool_result.to_json()[:200]}...")
                messages.extend(tool_result.get_claude_messages(tool_use.id, response.content))
                return tool_result
            else:
                return AiToolResult.from_text(response.content[0].text)

        except Exception as e:
            logger.error(f"Claude API error: {str(e)}", exc_info=True)
            raise

    async def process_tool_call(self, tool_name: str, tool_input: dict, context: ContextTypes.DEFAULT_TYPE) -> AiToolResult:
        try:
            handler = self.tool_handler.get_handler(tool_name)
            if not handler:
                logger.error(f"Unknown tool: {tool_name}")
                return AiToolResult.from_error(f"Unknown tool: {tool_name}")

            logger.debug(f"Processing tool call: {tool_name} with input: {json.dumps(tool_input, indent=2)}")

            if tool_name == "recognize_song" :
                result = await handler(tool_input, context.user_data)
            elif tool_name == "generate_audio_fragment":
                result = await handler(tool_input, context.user_data)
                if result.success:
                    audio_bytes = result.get_audio_bytes()
                    audio_file = io.BytesIO(audio_bytes)
                    audio_file.name = 'tts_audio.mp3'
                    await context.bot.send_audio(chat_id=context._chat_id, audio=audio_file)
                return result
            elif tool_name == "handle_merge_audio":
                result = await handler(tool_input)
                if result.success:
                    audio_bytes = result.get_audio_bytes()
                    audio_file = io.BytesIO(audio_bytes)
                    audio_file.name = 'merged_audio.mp3'
                    await context.bot.send_audio(chat_id=context._chat_id, audio=audio_file)
                return result
            else:
                result = await handler(tool_input)

            logger.debug(f"Tool call result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in tool call: {e}", exc_info=True)
            return AiToolResult.from_exception(e)
