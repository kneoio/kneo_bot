from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
import tempfile
import os
from services.shazam_client import ShazamAPIClient
from services.google_tts_client import GoogleTTSClient
from services.file_processor import LocalAudioProcessor
from utils.logger import logger

shazam_client = ShazamAPIClient()
tts_client = GoogleTTSClient()
audio_processor = LocalAudioProcessor()


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    temp_files = []
    try:
        file = update.message.audio
        if not file:
            return

        file_obj = await context.bot.get_file(file.file_id)
        file_data = await file_obj.download_as_bytearray()

        await update.message.reply_text("🎵 Analyzing audio...")
        metadata = await shazam_client.detect_song(file_data)

        if metadata:
            # Create temp files for processing
            speech_file = tempfile.mktemp(suffix='.mp3')
            song_file = tempfile.mktemp(suffix='.mp3')
            temp_files.extend([speech_file, song_file])

            # Save song to temp file
            with open(song_file, 'wb') as f:
                f.write(file_data)

            tts_text = f"This is {metadata['title']} by {metadata['artist']} <break time='1.0s'/>"
            speech_data = await tts_client.synthesize_speech(tts_text)

            if speech_data:
                with open(speech_file, 'wb') as f:
                    f.write(speech_data)

                # Merge files
                merged_data = audio_processor.merge_audio_files(speech_file, song_file)

                if merged_data:
                    await update.message.reply_audio(
                        merged_data,
                        filename=f"{metadata['artist']} - {metadata['title']} (with intro).mp3"
                    )
                    await update.message.reply_text(
                        f"✅ Track identified:\n"
                        f"Title: {metadata['title']}\n"
                        f"Artist: {metadata['artist']}\n"
                        f"Album: {metadata['album']}\n"
                        f"Genre: {metadata['genre']}"
                    )
                    return

            await update.message.reply_text("❌ Error processing audio")
        else:
            await update.message.reply_text("❌ Could not identify the song")

    except Exception as e:
        logger.error(f"Error in handle_file: {str(e)}")
        await update.message.reply_text("❌ Error processing file")

    finally:
        # Clean up temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Error cleaning up temp file {temp_file}: {str(e)}")