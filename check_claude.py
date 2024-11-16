# test_claude.py

import os
import anthropic
from dotenv import load_dotenv

from models.claude_message import ClaudeMessage

load_dotenv()


def test_claude():
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = ClaudeMessage.user_message("Hello! How are you?")

    response = client.messages.create(
        model=os.getenv("AI_MODEL"),
        max_tokens=1024,
        messages=[message.to_dict()]
    )

    print(response.content[0].text)


if __name__ == "__main__":
    test_claude()