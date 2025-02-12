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
    CallbackQueryHandler,
    filters,
)
from . import commands

async def handle_health(request):
    """Simple health check endpoint."""
    return web.Response(text="ok")

async def main():
    token = os.environ.get("BOT_TOKEN")
    webhook_url_base = os.environ.get("WEBHOOK_URL")  # e.g. "https://your-bot-domain.koyeb.app"
    if not token or not webhook_url_base:
        raise ValueError("BOT_TOKEN and WEBHOOK_URL environment variables must be set!")

    telegram_app = ApplicationBuilder().token(token).build()

    # Register basic command handlers.
    telegram_app.add_handler(CommandHandler("start", commands.start))
    telegram_app.add_handler(CommandHandler("view_thumbnail", commands.view_thumbnail))
    
    # Conversation for setting the thumbnail.
    thumb_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_thumbnail", commands.set_thumbnail_command)],
        states={
            commands.SET_THUMBNAIL: [MessageHandler(filters.PHOTO, commands.photo_handler)]
        },
        fallbacks=[CommandHandler("cancel", commands.cancel)]
    )
    telegram_app.add_handler(thumb_conv_handler)

    # Conversation for document handling.
    doc_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Document.ALL, commands.handle_document)],
        states={
            commands.CHOICE: [CallbackQueryHandler(commands.rename_choice_callback)],
            commands.NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, commands.new_name_handler)]
        },
        fallbacks=[CommandHandler("cancel", commands.cancel)]
    )
    telegram_app.add_handler(doc_conv_handler)

    # IMPORTANT: Initialize and start the Telegram application.
    await telegram_app.initialize()
    await telegram_app.start()

    # Set webhook URL.
    full_webhook_url = webhook_url_base.rstrip("/") + "/" + token
    await telegram_app.bot.set_webhook(url=full_webhook_url)
    print(f"Webhook set to: {full_webhook_url}")

    # Set up the aiohttp web application.
    app = web.Application()

    async def handle_webhook(request):
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400, text="Invalid request")
        update = Update.de_json(data, telegram_app.bot)
        asyncio.create_task(telegram_app.process_update(update))
        return web.Response(text="ok")

    app.router.add_post(f"/{token}", handle_webhook)
    app.router.add_get("/", handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    print("Webhook server started on port 8000")
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
