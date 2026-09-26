import pyrogram
from .start import start_handler, tiktok_callback_handler
from .ping import ping_handler
from .tiktok import tiktok_handler
from .donation import donation_handler


def register_handlers(bot: pyrogram.Client):
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
    bot.add_handler(
        handler=pyrogram.handlers.callback_query_handler.CallbackQueryHandler(
            callback=tiktok_callback_handler,
            filters=pyrogram.filters.regex(r"download_tiktok"),
        )
    )
