import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
MONGO_URI = os.environ.get("MONGO_URI", "") 

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["autoban_bot_db"]
groups_col = db["groups"]

bot = Client(
    'left_ban_bot',
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

@bot.on_message(filters.command('start') & filters.private)
async def start(client, message: Message):
    bot_user = await client.get_me()
    text = '👋 Hey, I am Autoban Bot \n\nI Can Ban a Member After Leaving The group.'
    await message.reply(text, quote=True)

# ⚠️ Service Message (လူထွက်သွားစဉ် ပေါ်လာသော စနစ်စာသား) ကို ဖမ်း၍ Ban ခြင်း
@bot.on_message(filters.left_chat_member & filters.group)
async def ban_on_left_service_message(client, message: Message):
    try:
        chat_id = message.chat.id
        left_user = message.left_chat_member
        
        if left_user and left_user.id != client.me.id:
            # ထွက်သွားသူကို ချက်ချင်း Ban မည်
            await client.ban_chat_member(chat_id, left_user.id)
            print(f"✅ Service Message ဖြင့် Banned Left User: {left_user.id} ({left_user.first_name}) in Chat: {chat_id}")
            
            # (ချန်လှပ်နိုင်သည်) ထွက်သွားကြောင်း ပြတဲ့ Service Message ကိုပါ ဖျက်လိုပါက
            await message.delete()
            
    except Exception as e:
        print(f"❌ Error in ban_on_left_service_message: {e}")

@bot.on_message(filters.group, group=-1)
async def track_groups(client, m: Message):
    if not groups_col.find_one({"chat_id": m.chat.id}):
        groups_col.insert_one({"chat_id": m.chat.id})

bot.run()
