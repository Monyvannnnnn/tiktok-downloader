import pyrogram
from services.logger import log_activity


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
