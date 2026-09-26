import pyrogram
from config import api_id, api_hash, token_bot

bot = pyrogram.Client(
    name="tiktok-bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=token_bot,
)
