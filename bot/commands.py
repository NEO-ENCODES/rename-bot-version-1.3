# bot/commands.py

import os
from telethon import Button
from .persistence import load_thumbnail_data, save_thumbnail_data

# Load persistent thumbnail data
thumbnail_data = load_thumbnail_data()

def get_thumb_path(user_id):
    """Return a file path for storing the user's thumbnail."""
    if not os.path.exists("thumbs"):
        os.makedirs("thumbs")
    return f"thumbs/{user_id}.jpg"

# -----------------------------
# Command Handlers
# -----------------------------

async def cmd_start(event):
    await event.reply("Welcome!\nUse /view_thumbnail to see your current thumbnail.\nUse /set_thumbnail to set a new thumbnail.")

async def cmd_view_thumbnail(event):
    user_id = str(event.sender_id)
    if user_id not in thumbnail_data:
        await event.reply("You have no thumbnail")
    else:
        thumb_path = thumbnail_data[user_id]
        if os.path.exists(thumb_path):
            await event.reply(file=thumb_path)
        else:
            await event.reply("Thumbnail file not found.")

async def cmd_set_thumbnail(event):
    # Mark that this user is awaiting a thumbnail
    if not hasattr(event.client, "_awaiting_thumbnail"):
        event.client._awaiting_thumbnail = {}
    event.client._awaiting_thumbnail[str(event.sender_id)] = True
    await event.reply("Please send me the photo you want to set as your thumbnail.")

def check_thumbnail_photo(event):
    # Only process if the message has a photo and the user is flagged as awaiting a thumbnail
    if event.message.photo:
        if hasattr(event.client, "_awaiting_thumbnail"):
            return str(event.sender_id) in event.client._awaiting_thumbnail
    return False

async def handle_thumbnail_photo(event):
    user_id = str(event.sender_id)
    thumb_path = get_thumb_path(user_id)
    # Download the photo (the highest quality version is downloaded by default)
    await event.message.download_media(file=thumb_path)
    thumbnail_data[user_id] = thumb_path
    save_thumbnail_data(thumbnail_data)
    event.client._awaiting_thumbnail.pop(user_id, None)
    await event.reply("Thumbnail set successfully!")

# -----------------------------
# Document Handling
# -----------------------------

async def handle_document(event):
    """When a document is sent, check for thumbnail and ask if the user wants to rename it."""
    user_id = str(event.sender_id)
    if user_id not in thumbnail_data:
        await event.reply("Set thumbnail first")
        return
    # Store document info in client state
    if not hasattr(event.client, "_doc_state"):
        event.client._doc_state = {}
    event.client._doc_state[user_id] = {"document": event.message.document, "message": event.message}
    buttons = [
        [Button.inline("Yes", b"rename_yes"), Button.inline("No", b"rename_no")]
    ]
    await event.reply("Do you want to rename the document?", buttons=buttons)

async def callback_handler(event):
    """Handle the inline button press for renaming decision."""
    user_id = str(event.sender_id)
    data = event.data.decode("utf-8")
    if data == "rename_yes":
        # Mark that we await a new file name
        if hasattr(event.client, "_doc_state") and user_id in event.client._doc_state:
            event.client._doc_state[user_id]["awaiting_new_name"] = True
        await event.edit("Please send the new file name.")
    elif data == "rename_no":
        await event.edit("Processing your document with original file name.")
        await process_document(event, new_name=None)
        if hasattr(event.client, "_doc_state"):
            event.client._doc_state.pop(user_id, None)

def check_new_name(event):
    """Check if this message should be interpreted as a new file name for a document."""
    user_id = str(event.sender_id)
    if hasattr(event.client, "_doc_state") and user_id in event.client._doc_state:
        if event.message.message and event.message.message.strip():
            if event.client._doc_state[user_id].get("awaiting_new_name"):
                return True
    return False

async def handle_new_name(event):
    user_id = str(event.sender_id)
    new_name = event.message.message.strip()
    await event.reply(f"Processing your document with new file name: {new_name}")
    await process_document(event, new_name=new_name)
    if hasattr(event.client, "_doc_state"):
        event.client._doc_state.pop(user_id, None)

async def process_document(event, new_name=None):
    """
    Download the document and re-send it with the desired filename and the user's thumbnail.
    This userbot can download large files because it uses a full client session.
    """
    from io import BytesIO
    user_id = str(event.sender_id)
    if not hasattr(event.client, "_doc_state") or user_id not in event.client._doc_state:
        return
    doc = event.client._doc_state[user_id]["document"]
    # Create a downloads directory if not exists
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    download_path = f"downloads/{user_id}_{doc.id}_{doc.file_name}"
    await event.client.download_media(doc, file=download_path)
    final_name = new_name if new_name else doc.file_name
    # Get the thumbnail file path from persistence
    thumb_path = thumbnail_data.get(user_id)
    await event.reply("Uploading file, please wait...")
    # Send the file with the new filename as caption and attach the thumbnail (if available).
    # Note: The 'thumb' parameter works only if using TDLib; with MTProto it might be ignored.
    await event.client.send_file(
        event.chat_id,
        download_path,
        caption=final_name,
        thumb=thumb_path
    )
    os.remove(download_path)
