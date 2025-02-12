# bot/main.py

import os
import asyncio
from telethon import TelegramClient, events, Button
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_name = os.environ.get("SESSION") or "userbot"
client = TelegramClient(session_name, api_id, api_hash)

from bot import commands

async def main():
    # Ensure the client connects properly
    await client.start()
    
    # Command handlers
    client.add_event_handler(commands.cmd_start, events.NewMessage(pattern='/start'))
    client.add_event_handler(commands.cmd_view_thumbnail, events.NewMessage(pattern='/view_thumbnail'))
    client.add_event_handler(commands.cmd_set_thumbnail, events.NewMessage(pattern='/set_thumbnail'))
    
    # Handler for photo messages that are meant for thumbnail setting
    client.add_event_handler(commands.handle_thumbnail_photo, events.NewMessage(func=commands.check_thumbnail_photo))
    
    # Handler for document messages (for renaming)
    client.add_event_handler(commands.handle_document, events.NewMessage(func=lambda e: e.message.document is not None))
    
    # Callback query handler for rename decision buttons
    client.add_event_handler(commands.callback_handler, events.CallbackQuery)
    
    # Handler for new messages that should be interpreted as new file names
    client.add_event_handler(commands.handle_new_name, events.NewMessage(func=commands.check_new_name))
    
    print("Userbot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
