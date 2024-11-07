import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler

from bot.constants import CONFIRM_REGISTRATION
from models.Event import Event, Precision, EventType
from services.user_storage import UserStorageClient
from services.event_repository import EventRepository

logger = logging.getLogger(__name__)

user_client = UserStorageClient()
event_repo = EventRepository()

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


async def handle_registration(update: Update):
    if update.message.text.lower() == 'yes':
        user = update.effective_user
        result = user_client.register_user(user.username)
        msg = "Registration successful!" if result else "Registration failed. Try again."
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Registration cancelled.")
    return ConversationHandler.END


async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user_client.check_user(user.username):
        await update.message.reply_text("Please register first using /start")
        return

    events = event_repo.check_what_we_have_today()
    if not events:
        await update.message.reply_text("No events for today!")
        return

    message = "Today's events:\n"
    for event in events:
        message += f"\n- {event.description} at {event.around} ({event.precision})"

    await update.message.reply_text(message)


async def add_random_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    event = Event(
        around=now,
        precision=Precision.EXACT,  # Changed
        description="Random test event",
        type=EventType.REMINDER,  # Changed
        author=update.effective_user.username,
        createdAt=now
    )

    return await add_event(update, context, event)


async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE, event: Event):
    user = update.effective_user
    if not user_client.check_user(user.username):
        await update.message.reply_text("Please register first using /start")
        return

    event_id = event_repo.add_event(event)
    await update.message.reply_text(f"Event added: {event.description} at {event.around}")