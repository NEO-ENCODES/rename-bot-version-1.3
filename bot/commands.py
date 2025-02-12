# bot/commands.py

from telegram import Update
from telegram.ext import ConversationHandler
from .persistence import load_thumbnail_data, save_thumbnail_data

# Load thumbnail data at module level
thumbnail_data = load_thumbnail_data()

# Conversation state for /set_thumbnail
WAIT_FOR_PHOTO = 1

async def start(update: Update, context):
    """Handle the /start command."""
    await update.message.reply_text(
        "Welcome!\n"
        "Use /view_thumbnail to see your current thumbnail.\n"
        "Use /set_thumbnail to set a new thumbnail."
    )

async def view_thumbnail(update: Update, context):
    """Handle the /view_thumbnail command."""
    user_id = str(update.effective_user.id)
    if user_id not in thumbnail_data:
        await update.message.reply_text("You have no thumbnail")
    else:
        thumbnail = thumbnail_data[user_id]
        await update.message.reply_photo(photo=thumbnail)

async def set_thumbnail_command(update: Update, context):
    """Initiate thumbnail setting by asking the user to send a photo."""
    await update.message.reply_text("Please send the picture you want to set as your thumbnail.")
    return WAIT_FOR_PHOTO

async def photo_handler(update: Update, context):
    """Handle the photo sent by the user and save the highest quality version."""
    user_id = str(update.effective_user.id)
    photo_list = update.message.photo
    if not photo_list:
        await update.message.reply_text("No photo detected. Please send a valid photo.")
        return WAIT_FOR_PHOTO

    # The last photo in the list is usually the highest quality.
    highest_quality_photo = photo_list[-1]
    file_id = highest_quality_photo.file_id

    # Save the file_id as the user's thumbnail.
    thumbnail_data[user_id] = file_id
    save_thumbnail_data(thumbnail_data)

    await update.message.reply_text("Thumbnail set successfully!")
    return ConversationHandler.END

async def cancel(update: Update, context):
    """Cancel the current conversation."""
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END
