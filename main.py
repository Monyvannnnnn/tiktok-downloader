import asyncio
import os
import json
from collections import deque
from datetime import datetime, timezone
import utils
import pathlib
import pyrogram
import databases
import sqlalchemy
import tiktok_downloader
from load import *
from models import users, videos, metadata

cwd = pathlib.Path(__file__).parent

bot = pyrogram.Client(
    name="tiktok-bot", api_id=api_id, api_hash=api_hash, bot_token=token_bot
)

recent_logs = deque(maxlen=200)


def log_activity(text: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    recent_logs.appendleft({"time": timestamp, "text": text})
    print(f"[{timestamp}] {text}")


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
    log_activity(f"{userid} {full_name} - /ping")
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
    log_activity(
        f"video id : {video_id}, author id : {author_id}, username : {author_username}"
    )
    log_activity(f"video url : {video_url}")
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
            log_activity("using cache database !")
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
    if images and len(images) > 0:
        log_activity(f"Downloading photo slideshow ({len(images)} images)...")
        try:
            await client.delete_messages(chat_id=userid, message_ids=msgid)
        except Exception:
            pass

        caption_text = f"Successfully downloaded {len(images)} photo(s)\n"
        if link_length > 40:
            caption_text += f"\n{source_link}\n"
        caption_text += "\nPowered by @TiktokVideoDownloaderIDBot"

        # Try sending direct image URLs first
        media_group = []
        for i, img_url in enumerate(images[:10]):
            if i == 0:
                media_group.append(pyrogram.types.InputMediaPhoto(media=img_url, caption=caption_text))
            else:
                media_group.append(pyrogram.types.InputMediaPhoto(media=img_url))

        try:
            await client.send_media_group(chat_id=userid, media=media_group)
            return
        except Exception as e:
            log_activity(f"Direct image URL media group notice: {e}, downloading images locally...")
            local_files = []
            try:
                for idx, img_url in enumerate(images[:10]):
                    img_path = cwd.joinpath(f"{video_id}_{idx}.jpg")
                    try:
                        await tiktok_downloader.get_content(url=img_url, output=str(img_path))
                        if img_path.exists() and img_path.stat().st_size > 0:
                            local_files.append(img_path)
                    except Exception as err:
                        log_activity(f"Failed to download image {idx}: {err}")

                if local_files:
                    local_media_group = []
                    for idx, img_path in enumerate(local_files):
                        if idx == 0:
                            local_media_group.append(pyrogram.types.InputMediaPhoto(media=str(img_path), caption=caption_text))
                        else:
                            local_media_group.append(pyrogram.types.InputMediaPhoto(media=str(img_path)))
                    await client.send_media_group(chat_id=userid, media=local_media_group)
                    return
            except Exception as ex:
                log_activity(f"Local image download error: {ex}")
            finally:
                for f in local_files:
                    f.unlink(missing_ok=True)

    now = int(datetime.now(timezone.utc).timestamp())
    output = cwd.joinpath(f"{video_id}.mp4")
    dl_success = False
    if video_url and len(video_url) > 0:
        log_activity("try download with main tiktok")
        try:
            await tiktok_downloader.get_content(
                url=video_url, output=str(output), cookies=cookies
            )
            dl_success = output.exists() and output.stat().st_size > 0
        except Exception as e:
            log_activity(f"main tiktok download error: {e}")

    if not dl_success:
        log_activity("try download with musicaldown !")
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
    log_activity(f"{userid} {full_name} - {text}")
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


async def handle_health_check(reader, writer):
    try:
        request_line = await reader.readline()
        while True:
            header_line = await reader.readline()
            if not header_line or header_line == b"\r\n":
                break

        req_str = request_line.decode("utf-8", errors="ignore")
        if "/api/logs" in req_str:
            body = json.dumps(list(recent_logs)).encode("utf-8")
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + body)
        else:
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScrollSaver - Live Activity Log</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            padding: 24px;
            min-height: 100vh;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 18px 24px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .title { font-size: 18px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(35, 134, 54, 0.15);
            color: #3fb950;
            border: 1px solid rgba(63, 185, 80, 0.3);
            font-size: 13px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 20px;
        }
        .dot { width: 8px; height: 8px; background: #3fb950; border-radius: 50%; animation: pulse 1.8s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }
        .card-header {
            padding: 14px 20px;
            border-bottom: 1px solid var(--border-color);
            font-size: 14px;
            font-weight: 600;
            color: #8b949e;
            display: flex;
            justify-content: space-between;
        }
        .logs-container {
            max-height: 550px;
            overflow-y: auto;
            font-family: 'Fira Code', monospace;
            font-size: 13px;
            padding: 8px;
        }
        .log-item {
            display: flex;
            gap: 14px;
            padding: 8px 12px;
            border-radius: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            word-break: break-all;
        }
        .log-item:hover { background: rgba(255, 255, 255, 0.04); }
        .log-time { color: var(--text-muted); flex-shrink: 0; font-size: 12px; }
        .log-text { color: #e6edf3; flex-grow: 1; }
        .empty-state { text-align: center; padding: 40px; color: var(--text-muted); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🤖 ScrollSaver Live Terminal Dashboard</div>
            <div class="badge"><span class="dot"></span> Bot Active</div>
        </div>
        <div class="card">
            <div class="card-header">
                <span>Live Activity Stream</span>
                <span>Auto-refreshing every 2s</span>
            </div>
            <div class="logs-container" id="logs-list">
                <div class="empty-state">Loading activity logs...</div>
            </div>
        </div>
    </div>
    <script>
        async function fetchLogs() {
            try {
                const res = await fetch('/api/logs');
                const logs = await res.json();
                const container = document.getElementById('logs-list');
                if (!logs || logs.length === 0) {
                    container.innerHTML = '<div class="empty-state">No activity logged yet. Send /start or a TikTok link in Telegram!</div>';
                    return;
                }
                container.innerHTML = logs.map(item => `
                    <div class="log-item">
                        <span class="log-time">[${item.time} UTC]</span>
                        <span class="log-text">${escapeHtml(item.text)}</span>
                    </div>
                `).join('');
            } catch (err) {
                console.error("Fetch error:", err);
            }
        }
        function escapeHtml(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }
        fetchLogs();
        setInterval(fetchLogs, 2000);
    </script>
</body>
</html>"""
            body = html_content.encode("utf-8")
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + body)
        await writer.drain()
    except Exception as e:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    log_activity("start bot !")
    port = int(os.environ.get("PORT", 8080))
    try:
        await asyncio.start_server(handle_health_check, "0.0.0.0", port)
        log_activity(f"HTTP health server started on port {port}")
    except Exception as e:
        log_activity(f"Port binding note: {e}")

    try:
        db_engine = sqlalchemy.create_engine(DATABASE.replace("+aiomysql", "").replace("+aiosqlite", ""))
        metadata.create_all(db_engine)
    except Exception as e:
        log_activity(f"Database table check/creation notice: {e}")
    await bot.start()
    me = await bot.get_me()
    botname = me.first_name
    botuname = me.username
    log_activity(f"Bot name : {botname}")
    log_activity(f"Bot username : {botuname}")
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
