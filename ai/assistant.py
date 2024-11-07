import json
import logging
import anthropic
from telegram import Update
from telegram.ext import ContextTypes
from bot.constants import UNDEFINED
from ai.prompts.events import EVENT_MANAGER_PROMPT
from ai.tools import ToolHandler

logger = logging.getLogger(__name__)


class AIHandler:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.tools = self._load_tool_definitions()
        self.tool_handler = ToolHandler()

    def _load_tool_definitions(self):
        try:
            with open('tools_definition/base_tools.json', 'r') as file:
                data = json.load(file)
                return data['tools']
        except Exception as e:
            logger.error(f"Error loading tool definitions: {e}")
            return []

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        message_text = update.message.text

        response = await self.handle_conversation(
            chat_id, user_id, username,
            [{"role": "user", "content": message_text}],
            EVENT_MANAGER_PROMPT
        )

        await update.message.reply_text(
            response if response != UNDEFINED else "I'm not sure how to help with that."
        )

    async def handle_conversation(self, chat_id: str, user_id: str, username: str,
                                  messages: list, system_prompt: str) -> str:
        while True:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=messages,
                system=system_prompt,
                tools=self.tools
            )

            if response.stop_reason == "tool_use":
                tool_use = response.content[-1]
                tool_name = tool_use.name
                tool_input = tool_use.input

                logger.info(f"Tool use: {tool_name}")
                logger.info(f"Tool input: {tool_input}")

                tool_result = await self.process_tool_call(tool_name, tool_input)
                logger.info(f"Tool result: {tool_result}")

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

    async def process_tool_call(self, tool_name: str, tool_input: dict) -> str:
        try:
            handler_map = {
                "check_user": self.tool_handler.handle_check_user,
                "register_user": self.tool_handler.handle_register_user,
                "add_event": self.tool_handler.handle_add_event,
                "check_today_events": self.tool_handler.handle_check_today_events
            }

            handler = handler_map.get(tool_name)
            if handler:
                return await handler(tool_input)

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