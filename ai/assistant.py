import json
import os
import anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from bot.constants import UNDEFINED
from ai.prompts.events import EVENT_MANAGER_PROMPT
from ai.tools import ToolHandler
from utils.logger import logger

load_dotenv()

def load_tool_definitions():
    try:
        with open('ai/tools_definition/base_tools.json', 'r') as file:
            data = json.load(file)
            logger.info(f"Loaded tools: {[t['name'] for t in data['tools']]}")
            return data['tools']
    except Exception as e:
        logger.error(f"Error loading tool definitions: {e}")
        return []

class Assistant:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.tools = load_tool_definitions()
        self.tool_handler = ToolHandler()
        logger.info("Assistant initialized")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_text = update.message.text
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        username = update.effective_user.username

        try:
            if update.message.audio:
                file_obj = await context.bot.get_file(update.message.audio.file_id)
                file_data = await file_obj.download_as_bytearray()
                context.user_data['current_audio'] = file_data.hex()
                logger.info(f"Audio file stored: {update.message.audio.file_name}")

            response = await self.handle_conversation(
                chat_id, user_id, username,
                [{"role": "user", "content": message_text}],
                EVENT_MANAGER_PROMPT,
                context
            )

            await update.message.reply_text(response if response != UNDEFINED else "I'm not sure how to help with that.")

        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("An error occurred")

    async def handle_conversation(self, chat_id: str, user_id: str, username: str,
                               messages: list, system_prompt: str, context: ContextTypes.DEFAULT_TYPE) -> str:
        while True:
            logger.info("Sending request to Claude")
            response = self.client.messages.create(
                model=os.getenv("AI_MODEL"),
                max_tokens=1024,
                messages=messages,
                system=system_prompt,
                tools=self.tools
            )

            if response.stop_reason == "tool_use":
                tool_use = response.content[-1]
                tool_name = tool_use.name
                tool_input = tool_use.input
                logger.info(f"Tool requested: {tool_name}")

                tool_result = await self.process_tool_call(tool_name, tool_input, context)
                logger.info(f"Tool result: {tool_result[:200]}...")

                messages.extend([
                    {"role": "assistant", "content": response.content},
                    {
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": str(tool_result)
                        }]
                    }
                ])
            else:
                return response.content[0].text

    async def process_tool_call(self, tool_name: str, tool_input: dict, context: ContextTypes.DEFAULT_TYPE) -> str:
        try:
            # For recognize_song, add audio data from context
            if tool_name == "recognize_song":
                tool_input['audio_data'] = context.user_data.get('current_audio', '')

            handler = self.tool_handler.get_handler(tool_name)
            if handler:
                return await handler(tool_input)

            logger.error(f"Unknown tool: {tool_name}")
            return json.dumps({
                "success": False,
                "metadata": None
            })

        except Exception as e:
            logger.error(f"Error in tool call: {e}")
            return json.dumps({
                "success": False,
                "metadata": None
            })