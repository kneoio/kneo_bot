import json
from dataclasses import dataclass


class AiToolResult:
    def __init__(self, success: bool, data: any = None):
        self.success = success
        self.data = data

    def to_json(self) -> str:
        return json.dumps({
            "success": self.success,
            "data": self.data
        })

    @staticmethod
    def from_json(json_str: str) -> 'AiToolResult':
        data = json.loads(json_str)
        return AiToolResult(
            success=data["success"],
            data=data.get("data")
        )

    @staticmethod
    def from_text(text: str) -> 'AiToolResult':
        return AiToolResult(True, text)

    @staticmethod
    def from_error(error_message: str) -> 'AiToolResult':
        return AiToolResult(False, {"error": error_message})

    @staticmethod
    def from_exception(e: Exception) -> 'AiToolResult':
        return AiToolResult(False, {
            "error": str(e),
            "type": type(e).__name__
        })

    @staticmethod
    def from_audio(audio_data: bytes, text_message: str = None) -> 'AiToolResult':
        return AiToolResult(True, {
            "audio_data": audio_data.hex() if audio_data else None,
            "text": text_message or "Audio generated successfully"
        })

    def get_audio_bytes(self) -> bytes:
        if self.success and isinstance(self.data, dict) and "audio_data" in self.data:
            return bytes.fromhex(self.data["audio_data"])
        return None

    def get_telegram_answer(self) -> str:
        if not self.success:
            if isinstance(self.data, dict) and "error" in self.data:
                return f"Error: {self.data['error']}"
            return "Operation failed"

        if isinstance(self.data, dict):
            return self.data.get("text", "Operation completed")

        if isinstance(self.data, str) and self.data:
            return self.data

        return "Operation completed"

    def get_claude_tool_result(self, tool_use_id: str) -> dict:
        return {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": self.to_json()
            }]
        }

    def get_claude_messages(self, tool_use_id: str, response_content: list) -> list:
        return [
            {"role": "assistant", "content": response_content},
            self.get_claude_tool_result(tool_use_id)
        ]
