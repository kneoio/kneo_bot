import os
from google.cloud import texttospeech
from dotenv import load_dotenv
from utils.logger import logger

class GoogleTTSClient:
    def __init__(self):
        load_dotenv()
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.client = texttospeech.TextToSpeechClient()

    async def synthesize_speech(self, text: str, voice_name: str = "en-US-Casual-K",
                                language_code: str = "en-US") -> bytes:
        try:
            # Check if text contains SSML tags
            if text.strip().startswith('<speak'):
                synthesis_input = texttospeech.SynthesisInput(ssml=text)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=text)

            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            logger.info(f"Speech synthesized for text: {text[:50]}...")
            return response.audio_content

        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None