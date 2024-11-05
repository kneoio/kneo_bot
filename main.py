import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, \
    CallbackContext

from bot.command__handler import list_events, start, handle_registration
from bot.constants import CONFIRM_REGISTRATION

load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_language(update, context):
    if len(context.args) > 0:
        language_code = context.args[0].lower()
        context.user_data['language_code'] = language_code
        await update.message.reply_text(f"Language set to {language_code}.")
    else:
        await update.message.reply_text("Please provide a valid language code (e.g., 'en', 'pt').")


async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


async def error_handler(update: object, context: CallbackContext):
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("An error occurred. Please try again.")


if __name__ == '__main__':
    logger.info("Starting the bot...")

    app = ApplicationBuilder().token(API_TOKEN).build()
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler('events', list_events))

    registration_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CONFIRM_REGISTRATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(registration_conv_handler)
    app.add_handler(CommandHandler('setlanguage', set_language))

    logger.info("Bot is running...")
    app.run_polling()