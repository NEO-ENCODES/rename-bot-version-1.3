import os
import asyncio
from aiohttp import web
from telethon import TelegramClient, events, Button

# Get credentials from environment variables
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_name = os.environ.get("SESSION") or "userbot"

# Create the Telethon client
client = TelegramClient(session_name, api_id, api_hash)

from bot import commands

async def run_bot():
    try:
        await client.start()
        print("Userbot is running...")
        # This call should block until disconnected.
        await client.run_until_disconnected()
    except Exception as e:
        print("Error in run_bot:", e)
        # If the bot disconnects or errors, wait indefinitely so the health server keeps the container alive.
        await asyncio.Event().wait()

async def run_health_server():
    app = web.Application()
    
    async def health_handler(request):
        return web.Response(text="ok")
    
    app.router.add_get('/', health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    print("Health server started on port 8000")
    await site.start()
    # Block forever to keep the server running.
    await asyncio.Event().wait()

async def main():
    # Register event handlers for Telethon
    client.add_event_handler(commands.cmd_start, events.NewMessage(pattern='/start'))
    client.add_event_handler(commands.cmd_view_thumbnail, events.NewMessage(pattern='/view_thumbnail'))
    client.add_event_handler(commands.cmd_set_thumbnail, events.NewMessage(pattern='/set_thumbnail'))
    client.add_event_handler(commands.handle_thumbnail_photo, events.NewMessage(func=commands.check_thumbnail_photo))
    client.add_event_handler(commands.handle_document, events.NewMessage(func=lambda e: e.message.document is not None))
    client.add_event_handler(commands.callback_handler, events.CallbackQuery)
    client.add_event_handler(commands.handle_new_name, events.NewMessage(func=commands.check_new_name))
    
    # Run both the bot and the health server concurrently.
    await asyncio.gather(
        run_bot(),
        run_health_server()
    )

if __name__ == '__main__':
    asyncio.run(main())
