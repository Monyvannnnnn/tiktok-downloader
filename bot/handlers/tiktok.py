from datetime import datetime, timezone
import pyrogram
import databases
from config import DATABASE, BASE_DIR
from database.models import users, videos
from services.downloader import get_video_detail, get_content, musicaldown
from services.logger import log_activity


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
        await get_video_detail(tiktok_url)
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
    retext += "\nPowered by @thescrollsaver_bot"
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
        caption_text += "\nPowered by @thescrollsaver_bot"

        if len(images) == 1:
            img_url = images[0]
            try:
                await client.send_photo(chat_id=userid, photo=img_url, caption=caption_text, reply_markup=rekey)
                return
            except Exception as e:
                log_activity(f"Direct send_photo notice: {e}, downloading image locally...")
                img_path = BASE_DIR.joinpath(f"{video_id}_0.jpg")
                try:
                    await get_content(url=img_url, output=str(img_path))
                    if img_path.exists() and img_path.stat().st_size > 0:
                        await client.send_photo(chat_id=userid, photo=str(img_path), caption=caption_text, reply_markup=rekey)
                        return
                except Exception as ex:
                    log_activity(f"Local send_photo error: {ex}")
                finally:
                    img_path.unlink(missing_ok=True)
        else:
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
                        img_path = BASE_DIR.joinpath(f"{video_id}_{idx}.jpg")
                        try:
                            await get_content(url=img_url, output=str(img_path))
                            if img_path.exists() and img_path.stat().st_size > 0:
                                local_files.append(img_path)
                        except Exception as err:
                            log_activity(f"Failed to download image {idx}: {err}")

                    if local_files:
                        if len(local_files) == 1:
                            await client.send_photo(chat_id=userid, photo=str(local_files[0]), caption=caption_text, reply_markup=rekey)
                        else:
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
    output = BASE_DIR.joinpath(f"{video_id}.mp4")
    dl_success = False
    if video_url and len(video_url) > 0:
        log_activity("try download with main tiktok")
        try:
            await get_content(
                url=video_url, output=str(output), cookies=cookies
            )
            dl_success = output.exists() and output.stat().st_size > 0
        except Exception as e:
            log_activity(f"main tiktok download error: {e}")

    if not dl_success:
        log_activity("try download with musicaldown !")
        dl_success = await musicaldown(url=tiktok_url, output=str(output))

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
