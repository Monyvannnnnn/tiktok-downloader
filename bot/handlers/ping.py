import asyncio
import pyrogram
from services.logger import log_activity


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
