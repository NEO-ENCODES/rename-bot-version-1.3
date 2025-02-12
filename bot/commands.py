# bot/commands.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from .persistence import load_thumbnail_data, save_thumbnail_data

# Load thumbnail data at module level
thumbnail_data = load_thumbnail_data()

# Existing command handlers
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
        thumb = thumbnail_data[user_id]
        await update.message.reply_photo(photo=thumb)

async def set_thumbnail_command(update: Update, context):
    """Initiate thumbnail setting by asking the user to send a photo."""
    await update.message.reply_text("Please send the picture you want to set as your thumbnail.")
    return SET_THUMBNAIL

async def photo_handler(update: Update, context):
    """Handle the photo sent by the user and save the highest quality version."""
    user_id = str(update.effective_user.id)
    photo_list = update.message.photo
    if not photo_list:
        await update.message.reply_text("No photo detected. Please send a valid photo.")
        return SET_THUMBNAIL

    highest_quality_photo = photo_list[-1]
    file_id = highest_quality_photo.file_id
    thumbnail_data[user_id] = file_id
    save_thumbnail_data(thumbnail_data)

    await update.message.reply_text("Thumbnail set successfully!")
    return ConversationHandler.END

async def cancel(update: Update, context):
    """Cancel the current conversation."""
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# --- New Document Handling Conversation ---

# Conversation states for document renaming
CHOICE = 1
NEW_NAME = 2
SET_THUMBNAIL = 10  # for the set_thumbnail conversation

async def handle_document(update: Update, context):
    """Handle a document sent directly by the user."""
    document = update.message.document
    user_id = str(update.effective_user.id)
    if user_id not in thumbnail_data:
        await update.message.reply_text("Set thumbnail first")
        return ConversationHandler.END

    # Save the document in user_data for later use
    context.user_data["document"] = document

    # Ask if user wants to rename the document
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="rename_yes"),
         InlineKeyboardButton("No", callback_data="rename_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Do you want to rename the document?", reply_markup=reply_markup)
    return CHOICE

async def rename_choice_callback(update: Update, context):
    """Handle the inline button response for renaming choice."""
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == "rename_yes":
        await query.edit_message_text("Please send the new file name.")
        return NEW_NAME
    elif choice == "rename_no":
        await query.edit_message_text("Processing your document with original file name.")
        await process_document(update, context, new_name=None)
        return ConversationHandler.END

async def new_name_handler(update: Update, context):
    """Handle the new file name provided by the user."""
    new_name = update.message.text.strip()
    await update.message.reply_text(f"Processing your document with new file name: {new_name}")
    await process_document(update, context, new_name=new_name)
    return ConversationHandler.END

async def process_document(update: Update, context, new_name=None):
    """Download the document and re-send it with the desired filename and user's thumbnail."""
    from io import BytesIO
    document = context.user_data.get("document")
    if not document:
        return
    bot = context.bot
    # Download the document
    file_obj = await bot.get_file(document.file_id)
    data = await file_obj.download_as_bytearray()
    buffer = BytesIO(data)
    buffer.seek(0)
    filename = new_name if new_name else document.file_name

    # Retrieve user's thumbnail file id from persistence
    from .persistence import load_thumbnail_data
    thumb_data = load_thumbnail_data()
    user_id = str(update.effective_user.id)
    thumb_id = thumb_data.get(user_id)

    thumb_buffer = None
    if thumb_id:
        try:
            thumb_file_obj = await bot.get_file(thumb_id)
            thumb_bytes = await thumb_file_obj.download_as_bytearray()
            thumb_buffer = BytesIO(thumb_bytes)
            thumb_buffer.seek(0)
        except Exception as e:
            print("Failed to download thumbnail:", e)
            thumb_buffer = None

    # Use update.message if available, else use update.callback_query.message
    msg = update.message if update.message is not None else update.callback_query.message
    await msg.reply_document(document=buffer, filename=filename, thumb=thumb_buffer)
