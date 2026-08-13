import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

# Environment Variables
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
MONGO_URI = os.environ.get("MONGO_URI", "") 

# Database Setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["autoban_bot_db"]
groups_col = db["groups"]

# Bot Initialization
bot = Client(
    'left_ban_bot',
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


@bot.on_message(filters.command('start') & filters.private)
async def start(client, message: Message):
    bot_user = await client.get_me()
    bot_username = bot_user.username
    
    text = (
        '✨ 𝖧𝖾𝗒, 𝖨 𝖺𝗆 𝖠𝗎𝗍𝗈𝖻𝖺𝗇 𝖡𝗈𝗍 ⚡\n\n'
        '🚫 𝖨 𝖼𝖺𝗇 𝖺𝗎𝗍𝗈-𝖻𝖺𝗇 𝗆𝖾𝗆𝖻𝖾𝗋𝗌 𝗐𝗁𝗈 𝗅𝖾𝖺𝗏𝖾 𝗍𝗁𝖾 𝗀𝗋𝗈𝗎𝗉.\n\n'
        '⚠️ 𝖥𝗈𝗋 𝗉𝖾𝗋𝗌𝗈𝗇𝖺𝗅 𝗀𝗋𝗈𝗎𝗉𝗌 𝗈𝗇𝗅𝗒.'
    )
    
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ 𝖠𝖽𝖽 𝖬𝖾 𝖳𝗈 𝖸𝗈𝗎𝗋 𝖦𝗋𝗈𝗎𝗉 ➕", 
                    url=f"https://t.me/{bot_username}?startgroup=true"
                )
            ]
        ]
    )
    
    await message.reply(text, reply_markup=reply_markup, quote=True)



@bot.on_message(filters.left_chat_member & filters.group)
async def ban_on_left_service_message(client, message: Message):
    try:
        chat_id = message.chat.id
        left_user = message.left_chat_member
        
        if left_user and left_user.id != client.me.id:
            
            await client.ban_chat_member(chat_id, left_user.id)
            print(f"✅ Auto-Banned Left User: {left_user.id} ({left_user.first_name}) in Chat: {chat_id}")
            
            
            await message.delete()
            
    except Exception as e:
        print(f"❌ Error in ban_on_left_service_message: {e}")



@bot.on_message(filters.group, group=-1)
async def track_groups(client, m: Message):
    if not groups_col.find_one({"chat_id": m.chat.id}):
        groups_col.insert_one({"chat_id": m.chat.id})
        print(f"📝 New Group Added to Database: {m.chat.id}")



@bot.on_message(filters.command('broadcast') & filters.user(OWNER_ID))
async def broadcast(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply("သုံးစွဲပုံ - /broadcast ပို့ချင်သောစာ သို့မဟုတ် စာတစ်စောင်ကို reply ပြန်ပြီး /broadcast ဟု ရိုက်ပါ။")
        return

    msg_to_send = message.reply_to_message if message.reply_to_message else message
    text_mode = False if message.reply_to_message else True

    status_msg = await message.reply("📢 Broadcast စတင်ပို့ဆောင်နေပါပြီ...")
    success = 0
    failed = 0

    all_groups = groups_col.find()

    for group in all_groups:
        chat_id = group["chat_id"]
        try:
            if text_mode:
                broadcast_text = message.text.split(None, 1)[1]
                await client.send_message(chat_id, broadcast_text)
            else:
                await msg_to_send.copy(chat_id)
            success += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            failed += 1
            groups_col.delete_one({"chat_id": chat_id})
            print(f"❌ Failed to send to {chat_id} (Removed from DB): {e}")

    await status_msg.edit(f"📢 Broadcast ပို့ဆောင်ပြီးစီးပါပြီ!\n\n✅ အောင်မြင် - {success} ခု\n❌ ကျရှုံး - {failed} ခု")


# Run Bot
if __name__ == "__main__":
    bot.run()
