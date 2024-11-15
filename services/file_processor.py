import os
import tempfile
from utils.logger import logger
import subprocess
from dotenv import load_dotenv


class LocalAudioProcessor:
    def __init__(self):
        load_dotenv()
        self.ffmpeg_path = os.getenv("FFMPEG_PATH")

    def merge_audio_files(self, intro_audio: bytes, main_audio: bytes) -> bytes:
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as intro_file, \
                    tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as main_file, \
                    tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as output_file:

                # Write bytes to temp files
                intro_file.write(intro_audio)
                main_file.write(main_audio)
                intro_file.flush()
                main_file.flush()

                command = [
                    self.ffmpeg_path,
                    "-y",
                    "-i", intro_file.name,
                    "-i", main_file.name,
                    "-filter_complex",
                    "[0:a][1:a]concat=n=2:v=0:a=1[out]",
                    "-map", "[out]",
                    output_file.name
                ]

                result = subprocess.run(command, capture_output=True, text=True)

                if result.returncode != 0:
                    logger.error(f"FFmpeg error: {result.stderr}")
                    return None

                with open(output_file.name, 'rb') as f:
                    merged_data = f.read()

            # Cleanup temp files
            os.unlink(intro_file.name)
            os.unlink(main_file.name)
            os.unlink(output_file.name)

            return merged_data

        except Exception as e:
            logger.error(f"Error merging audio files: {e}")
            return None