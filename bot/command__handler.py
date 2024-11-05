import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler

from bot.constants import CONFIRM_REGISTRATION
from services.UserAPIClient import UserAPIClient

logger = logging.getLogger(__name__)

user_client = UserAPIClient()


def get_user_language(context):
    return context.user_data.get('language_code', 'en')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    language_code = get_user_language(context)

    existing_user = user_client.check_user(user.username)
    if existing_user:
        await update.message.reply_text(f"Welcome back {user.username}!")
        return ConversationHandler.END

    await update.message.reply_text(f"Hi {user.username}! Not registered. Reply 'yes' to register.")
    return CONFIRM_REGISTRATION


async def handle_registration(update: Update, context: CallbackContext):
    if update.message.text.lower() == 'yes':
        user = update.effective_user
        result = user_client.register_user(user.username)
        msg = "Registration successful!" if result else "Registration failed. Try again."
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Registration cancelled.")
    return ConversationHandler.END


async def list_events(update: Update, context: CallbackContext):
    user_name = update.effective_user.username
    if not user_client.check_user(user_name):
        await update.message.reply_text("Please register first using /start")
        return
    await update.message.reply_text(f"Listed events for {user_name}")