import asyncio
import pyrogram
from bot import bot, register_handlers
from database import init_db
from server import start_web_server
from services.logger import log_activity


async def main():
    log_activity("start bot !")
    await start_web_server()
    init_db()

    await bot.start()
    me = await bot.get_me()
    log_activity(f"Bot name : {me.first_name}")
    log_activity(f"Bot username : {me.username}")

    register_handlers(bot)

    await pyrogram.idle()
    await bot.stop()


if __name__ == "__main__":
    bot.run(main())
