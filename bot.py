import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
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

# Start Command
@bot.on_message(filters.command('start') & filters.private)
async def start(client, message: Message):
    bot_user = await client.get_me()
    bot_username = bot_user.username
    
    text = (
        ' Hey, I am Autoban Bot \n\n'
        'I Can Welcome Members and Ban Them After Leaving The group. \n\n'
        '⚠️ Warning- My use is for personal Groups.'
    )
    
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Add Me To Your Group ➕", 
                    url=f"https://t.me/{bot_username}?startgroup=true"
                )
            ]
        ]
    )
    
    await message.reply(text, reply_markup=reply_markup, quote=True)


# Handle Member Join & Auto-Ban on Leave
@bot.on_chat_member_updated()
async def handle_chat_member_updated(client, event: ChatMemberUpdated):
    try:
        chat_id = event.chat.id
        
        # 1. အဖွဲ့ဝင်အသစ် ဝင်လာသောအခါ Welcome ပို့ရန်
        if event.new_chat_member and event.new_chat_member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR]:
            if event.new_chat_member.user.id != client.me.id:
                if not event.old_chat_member or event.old_chat_member.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
                    user = event.new_chat_member.user
                    chat = event.chat
                    
                    user_mention = f"[{user.first_name}](tg://user?id={user.id})"
                    
                    welcome_text = (
                        f"╭━━━❖ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 ❖━━━╮\n\n"
                        f"👋 မင်္ဂလာပါ {user_mention} ခင်ဗျာ။\n"
                        f"✨ **{chat.title}** မှ နွေးထွေးစွာ ကြိုဆိုပါတယ် ✨\n\n"
                        f"📌 **အသိပေးချက် & စည်းကမ်းချက်များ:**\n"
                        f"• အချင်းချင်း လေးစားစွာ နေထိုင်ပေးပါ။\n"
                        f"• ⚠️ *ဤအုပ်စုမှ မိမိဆန္ဒအလျောက် ထွက်သွားပါက စနစ်အရ အလိုအလျောက် Ban (ပိတ်ပင်) ခံရမည်ဖြစ်ပါကြောင်း \n ယဉ်ကျေးစွာ အသိပေးအပ်ပါသည်။*\n\n"
                        f"╰━━━━━━━━━━━━━━━╯"
                    )
                    
                    await client.send_message(chat_id, welcome_text)

        # 2. အဖွဲ့ဝင် ထွက်သွားသည်နှင့် ချက်ချင်း Ban ရန် (Auto-Ban on Leave)
        if event.new_chat_member and event.new_chat_member.status == enums.ChatMemberStatus.LEFT:
            left_user = event.new_chat_member.user
            
            # Bot ကိုယ်တိုင် မဟုတ်မှသာ
            if left_user and left_user.id != client.me.id:
                # အဖွဲ့ဝင်ကို ချက်ချင်း Ban မည်
                await client.ban_chat_member(chat_id, left_user.id)
                print(f"✅ Auto-Banned Left User: {left_user.id} ({left_user.first_name}) in Chat: {chat_id}")
                
    except Exception as e:
        print(f"❌ Error in handle_chat_member_updated: {e}")


# Track Groups in Database
@bot.on_message(filters.group, group=-1)
async def track_groups(client, m: Message):
    if not groups_col.find_one({"chat_id": m.chat.id}):
        groups_col.insert_one({"chat_id": m.chat.id})
        print(f"📝 New Group Added to Database: {m.chat.id}")


# Broadcast System (Owner Only)
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
