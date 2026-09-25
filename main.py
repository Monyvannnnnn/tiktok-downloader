import asyncio
import utils
import pathlib
import pyrogram
import databases
import sqlalchemy
import tiktok_downloader
from load import *
from models import users, videos, metadata
from datetime import datetime, timezone

cwd = pathlib.Path(__file__).parent

bot = pyrogram.Client(
    name="tiktok-bot", api_id=api_id, api_hash=api_hash, bot_token=token_bot
)


async def start_handler(client: pyrogram.Client, message: pyrogram.types.Message):
    user = message.from_user or message.chat
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = user.username
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    userid = user.id
    text = message.text
    print(f"{userid} {full_name} - {text}")
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
    retext = f"""Welcome {full_name} to Tiktok Video Downloader Bot

How to use :

KH : របៀបប្រើប្រាស់ bot គឺដោយផ្ញាត់តំណភ្ជាប់ពីវីដេូតីកុដដែលអ្នកចង់ទាញយក។

EN : How to use the bot by simply sending the link of the tiktok video you want to download.
    """
    await client.send_message(chat_id=userid, text=retext, reply_to_message_id=msgid)
    return


async def ping_handler(client: pyrogram.Client, message: pyrogram.types.Message):
    user = message.from_user or message.chat
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    userid = user.id
    msg_id = message.id
    print(f"{userid} {full_name} - /ping")
    result = await client.send_message(
        chat_id=userid, text="Pong!", reply_to_message_id=msg_id
    )
    await asyncio.sleep(2)
    await client.delete_messages(chat_id=userid, message_ids=msg_id)
    await client.delete_messages(chat_id=userid, message_ids=result.id)


async def tiktok_handler(client: pyrogram.Client, message: pyrogram.types.Message):
    user = message.from_user or message.chat
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = user.username
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    userid = user.id
    text = message.text
    msgid = message.id
    print(f"{userid} {full_name} - {text}")
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
    tiktok_url = None
    if len(text.split("\n")) > 1:
        tiktok_url = text.split("\n")[0]
        if "tiktok" not in tiktok_url:
            retext = "The video link you sent may be wrong."
            await client.send_message(
                chat_id=userid, text=retext, reply_to_message_id=msgid
            )
            return
    else:
        tiktok_url = text
    video_id, author_id, author_username, video_url, images, cookies = (
        await utils.get_video_detail(tiktok_url)
    )
    print(
        f"video id : {video_id}, author id : {author_id}, username : {author_username}"
    )
    print(f"video url : {video_url}")
    if video_id is None:
        retext = "The tiktok video you want to download doesn't exist, it might be deleted or a private video."
        await client.send_message(
            chat_id=userid, text=retext, reply_to_message_id=msgid
        )
        return
    link_length = len(tiktok_url)
    source_link = f"[Video Source]({tiktok_url})"
    retext = f"Successfully download the video\n"
    if link_length > 40:
        retext += f"\n{source_link}\n"
    retext += "\nPowered by @TiktokVideoDownloaderIDBot"
    keylist = [
        [
            pyrogram.types.InlineKeyboardButton(text="Source Video", url=tiktok_url),
        ],
    ]
    rekey = pyrogram.types.InlineKeyboardMarkup(inline_keyboard=keylist)
    async with databases.Database(DATABASE) as database:
        query = (
            "SELECT * FROM videos WHERE video_id = :video_id AND author_id = :author_id"
        )
        values = {
            "video_id": video_id,
            "author_id": author_id,
        }
        result = await database.fetch_one(query=query, values=values)
        if result is not None:
            print("using cache database !")
            file_id = result.file_id
            file_unique_id = result.file_unique_id
            try:
                await client.delete_messages(chat_id=userid, message_ids=msgid)
            except Exception:
                pass
            await client.send_cached_media(
                chat_id=userid, file_id=file_id, caption=retext, reply_markup=rekey
            )
            return
    now = int(datetime.now(timezone.utc).timestamp())
    output = cwd.joinpath(f"{video_id}.mp4")
    dl_success = False
    if video_url and len(video_url) > 0:
        print("try download with main tiktok")
        try:
            await tiktok_downloader.get_content(
                url=video_url, output=str(output), cookies=cookies
            )
            dl_success = output.exists() and output.stat().st_size > 0
        except Exception as e:
            print(f"main tiktok download error: {e}")

    if not dl_success:
        print("try download with musicaldown !")
        dl_success = await tiktok_downloader.musicaldown(url=tiktok_url, output=str(output))

    if not dl_success or not output.exists() or output.stat().st_size == 0:
        retext = "Failed to download video. Please try again or provide another link."
        await client.send_message(chat_id=userid, text=retext, reply_to_message_id=msgid)
        return

    try:
        await client.delete_messages(chat_id=userid, message_ids=msgid)
    except Exception:
        pass

    result = await client.send_video(
        chat_id=userid, video=str(output), caption=retext, reply_markup=rekey
    )
    file_id = None
    file_unique_id = None
    media = getattr(result, "video", None) or getattr(result, "animation", None) or getattr(result, "document", None)
    if media:
        file_id = media.file_id
        file_unique_id = media.file_unique_id

    if file_id and file_unique_id:
        async with databases.Database(DATABASE) as database:
            query = videos.insert()
            values = {
                "author_id": author_id,
                "author_username": author_username,
                "video_id": video_id,
                "file_id": file_id,
                "file_unique_id": file_unique_id,
                "created_at": datetime.now(timezone.utc).replace(microsecond=0),
            }
            await database.execute(query=query, values=values)
    output.unlink(missing_ok=True)
    return


async def donation_handler(
    client: pyrogram.Client,
    message: pyrogram.types.Message | pyrogram.types.CallbackQuery,
):
    if isinstance(message, pyrogram.types.Message):
        user = message.from_user or message.chat
        userid = user.id
        text = message.text
    if isinstance(message, pyrogram.types.CallbackQuery):
        user = message.from_user
        userid = user.id
        text = message.data
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    print(f"{userid} {full_name} - {text}")
    retext = """If you like my work, you can support me through the link below.
    
International : https://sociabuzz.com/fawwazthoerif/tribe
Indonesia : https://trakteer.id/fawwazthoerif/tip

CRYPTO
USDT (TON) : `UQDicJd7KwBcxzqbn6agUc_KVl8BklzyvuKGxEVG7xuhnTFt`
    """
    await client.send_message(
        chat_id=userid, text=retext, disable_web_page_preview=True
    )
    return


import os


async def handle_health_check(reader, writer):
    writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 15\r\n\r\nBot is running!")
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    print(f"start bot !")
    port = int(os.environ.get("PORT", 8080))
    try:
        await asyncio.start_server(handle_health_check, "0.0.0.0", port)
        print(f"HTTP health server started on port {port}")
    except Exception as e:
        print(f"Port binding note: {e}")

    try:
        db_engine = sqlalchemy.create_engine(DATABASE.replace("+aiomysql", "").replace("+aiosqlite", ""))
        metadata.create_all(db_engine)
    except Exception as e:
        print(f"Database table check/creation notice: {e}")
    await bot.start()
    me = await bot.get_me()
    botname = me.first_name
    botuname = me.username
    print(f"Bot name : {botname}")
    print(f"Bot username : {botuname}")
    bot.add_handler(
        handler=pyrogram.handlers.message_handler.MessageHandler(
            callback=start_handler,
            filters=pyrogram.filters.command(commands=["start"]),
        )
    )
    bot.add_handler(
        handler=pyrogram.handlers.message_handler.MessageHandler(
            callback=ping_handler,
            filters=pyrogram.filters.regex(r"ping"),
        )
    )
    bot.add_handler(
        handler=pyrogram.handlers.message_handler.MessageHandler(
            callback=tiktok_handler,
            filters=pyrogram.filters.regex(r"tiktok"),
        )
    )
    bot.add_handler(
        handler=pyrogram.handlers.message_handler.MessageHandler(
            callback=donation_handler,
            filters=pyrogram.filters.regex(r"donation"),
        )
    )
    bot.add_handler(
        handler=pyrogram.handlers.callback_query_handler.CallbackQueryHandler(
            callback=donation_handler,
            filters=pyrogram.filters.regex(r"donation"),
        )
    )
    await pyrogram.idle()
    await bot.stop()


if __name__ == "__main__":
    bot.run(main())
