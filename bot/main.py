# bot/main.py

import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from bot import commands

async def handle_health(request):
    """Simple health check endpoint."""
    return web.Response(text="ok")

async def main():
    # Retrieve environment variables.
    token = os.environ.get("BOT_TOKEN")
    webhook_url_base = os.environ.get("WEBHOOK_URL")  # e.g., "https://your-bot-domain.koyeb.app"
    if not token or not webhook_url_base:
        raise ValueError("BOT_TOKEN and WEBHOOK_URL environment variables must be set!")

    # Create the Telegram bot application.
    telegram_app = ApplicationBuilder().token(token).build()

    # Set up the conversation handler for /set_thumbnail.
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_thumbnail", commands.set_thumbnail_command)],
        states={
            commands.WAIT_FOR_PHOTO: [MessageHandler(filters.PHOTO, commands.photo_handler)]
        },
        fallbacks=[CommandHandler("cancel", commands.cancel)],
    )

    # Register handlers.
    telegram_app.add_handler(CommandHandler("start", commands.start))
    telegram_app.add_handler(CommandHandler("view_thumbnail", commands.view_thumbnail))
    telegram_app.add_handler(conv_handler)

    # IMPORTANT: Initialize and start the Telegram application.
    await telegram_app.initialize()
    await telegram_app.start()

    # Construct the full webhook URL.
    full_webhook_url = webhook_url_base.rstrip("/") + "/" + token

    # Set the webhook with Telegram.
    await telegram_app.bot.set_webhook(url=full_webhook_url)
    print(f"Webhook set to: {full_webhook_url}")

    # Create an aiohttp web application.
    app = web.Application()

    async def handle_webhook(request):
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400, text="Invalid request")
        update = Update.de_json(data, telegram_app.bot)
        # Process the update asynchronously.
        asyncio.create_task(telegram_app.process_update(update))
        return web.Response(text="ok")

    # Register routes:
    # - POST /<BOT_TOKEN> for webhook updates.
    # - GET / for health checks.
    app.router.add_post(f"/{token}", handle_webhook)
    app.router.add_get("/", handle_health)

    # Start the aiohttp server on port 8000.
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    print("Webhook server started on port 8000")
    await site.start()

    # Run indefinitely.
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
