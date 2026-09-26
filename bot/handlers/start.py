from datetime import datetime, timezone
import pyrogram
import databases
from config import DATABASE
from database.models import users
from services.logger import log_activity


async def start_handler(client: pyrogram.Client, message: pyrogram.types.Message):
    user = message.from_user or message.chat
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = user.username
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    userid = user.id
    text = message.text
    log_activity(f"{userid} {full_name} - {text}")
    query = "SELECT * FROM users WHERE user_id = :userid"
    values = {"userid": userid}
    async with databases.Database(DATABASE) as database:
        result = await database.fetch_one(query=query, values=values)
        if result is None:
            query = users.insert()
            values = {
                "user_id": userid,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "created_at": datetime.now(timezone.utc).replace(microsecond=0),
            }
            await database.execute(query=query, values=values)
    msgid = message.id
    retext = f"""✨ **Welcome, {full_name}!**

📥 **TikTok Downloader Bot**

I can help you download TikTok videos (without watermark) and photo slideshows fast and easily!

💡 **Choose an option or send a link:**
Simply send me any TikTok video link directly, or click below!

⚡ **Features:**
• No Watermark TikTok Videos
• Photo Slideshow Albums
• Fast & HD Quality

Select an option below to start! 🚀"""

    keylist = [
        [
            pyrogram.types.InlineKeyboardButton(
                text="🎵 Download TikTok Video", callback_data="download_tiktok"
            ),
        ],
    ]
    rekey = pyrogram.types.InlineKeyboardMarkup(inline_keyboard=keylist)
    await client.send_message(
        chat_id=userid, text=retext, reply_to_message_id=msgid, reply_markup=rekey
    )
    return


async def tiktok_callback_handler(
    client: pyrogram.Client, callback_query: pyrogram.types.CallbackQuery
):
    user = callback_query.from_user
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    log_activity(f"{user.id} {full_name} - clicked Download TikTok button")
    await callback_query.answer(
        "Send any TikTok video or photo link here to download it! 🎵", show_alert=True
    )
    return
