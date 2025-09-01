from telethon import TelegramClient, events
from aiohttp import web
import logging
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
phone = os.getenv("PHONE")
DESTINATION_CHAT_ID = int(os.getenv("DESTINATION_CHAT_ID"))
SOURCE_CHAT_ID = int(os.getenv("SOURCE_CHAT_ID"))
KEYWORDS = ["ago palace", "ago", "festac", "isolo", "surulere", "amuwo", "mushin"]

def log_message(chat_id, message_text, keywords, timestamp):
    conn = sqlite3.connect('forwarded_messages.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                     (chat_id TEXT, message TEXT, keywords TEXT, timestamp DATETIME)''')
    cursor.execute('INSERT INTO messages VALUES (?, ?, ?, ?)',
                  (chat_id, message_text, ','.join(keywords), timestamp))
    conn.commit()
    conn.close()

client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage(chats=[SOURCE_CHAT_ID]))
async def handler(event):
    message_text = event.message.text.lower() if event.message.text else ""
    found_keywords = [kw for kw in KEYWORDS if kw.lower() in message_text]
    if found_keywords:
        chat = await event.get_chat()
        sender = await event.get_sender()
        notification = (
            f"Keyword(s) {', '.join(found_keywords)} found in {chat.title or 'Unknown Chat'} (Chat ID: {event.chat_id})\n"
            f"Message: {event.message.text}\n"
            f"From: {sender.first_name or 'Unknown'} (@{sender.username or 'No Username'})"
        )
        await client.forward_messages(DESTINATION_CHAT_ID, event.message)
        await client.send_message(DESTINATION_CHAT_ID, notification)
        log_message(event.chat_id, event.message.text, found_keywords, event.message.date)
        logger.info(f"Forwarded message with keywords: {found_keywords}")

async def webhook(request):
    return web.Response(text="Bot is alive")

app = web.Application()
app.router.add_get('/', webhook)

async def main():
    await client.start(phone=phone)
    logger.info("Client started")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    web.run_app(app, host='0.0.0.0', port=int(os.getenv("PORT", 8080)))
