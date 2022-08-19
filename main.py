from aiogram import Bot, Dispatcher, types, filters, exceptions
from aiogram.utils.executor import set_webhook as web_set_webhook
from aiogram.contrib.fsm_storage.files import JSONStorage

from keyboards import Keyboards
from utils import get_logger, get_config, save_config
from basic_data import TEXTS
from web_app import routes as webapp_routes, webapp_error_middleware

from logging import Logger
from aiohttp import web
from ssl import SSLContext, PROTOCOL_TLSv1_2
from json import loads

from typing import List


config_filename: str = "config.json"

config: dict = get_config(
    filename = config_filename
)


with open("static/food_items.json", "r") as file:
    food_items: List[dict] = loads(
        s = file.read()
    )


logger: Logger = get_logger(
    name = config["db_name"]
)


keyboards: Keyboards = Keyboards(
    texts = TEXTS["keyboards"],
    web_app_url = config["web"]["url"].format(
        route = "/"
    )
)


bot: Bot = Bot(
    token = config["bot_token"],
    parse_mode = types.ParseMode.HTML
)

dp: Dispatcher = Dispatcher(
    bot = bot,
    storage = JSONStorage(
        path = "states.json"
    )
)


async def on_startup(dp: Dispatcher) -> None:
    await dp.bot.set_webhook(
        url = config["web"]["url"].format(
            route = "/{token}".format(
                token = config["bot_token"]
            )
        )
    )


async def on_shutdown(dp: Dispatcher) -> None:
    await dp.bot.delete_webhook()


@dp.pre_checkout_query_handler()
async def pre_checkout_query_handler(pre_checkout_query: types.PreCheckoutQuery) -> None:
    order_data: List[dict] = loads(
        s = pre_checkout_query.invoice_payload.replace("\'", "\"")
    )

    total_amount: int = 0

    for order_item in order_data:
        id: int
        count: int
        
        id, count = map(int, order_item.split(":"))

        total_amount += food_items[id]["price"] * count * 100

    total_amount = int(total_amount)

    tip: int = 0

    try:
        tip = config["suggested_tip_amounts"][config["suggested_tip_amounts"].index(int(pre_checkout_query.total_amount - total_amount))]
    except IndexError:
        pass

    await bot.answer_pre_checkout_query(
        pre_checkout_query_id = pre_checkout_query.id,
        ok = total_amount == pre_checkout_query.total_amount - tip,
        error_message = "incorrect payment"
    )


@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment_handler(message: types.Message) -> None:
    await message.answer(
        text = TEXTS["thanks"]
    )


@dp.message_handler(commands=["start"])
async def start_command_handler(message: types.Message) -> None:
    await message.answer(
        text = TEXTS["start"],
        reply_markup = keyboards.order
    )


web_app: web.Application = web.Application()

web_app["bot"] = bot
web_app["bot_provider_token"] = config["bot_provider_token"]
web_app["food_items"] = food_items
web_app["suggested_tip_amounts"] = config["suggested_tip_amounts"]
web_app["logger"] = logger

web_app.middlewares.append(
    web.middleware(
        f = webapp_error_middleware
    )
)

web_app.add_routes(
    routes = webapp_routes
)

web_set_webhook(
    dispatcher = dp,
    webhook_path = "/{token}".format(
        token = config["bot_token"]
    ),
    skip_updates = False,
    on_startup = on_startup,
    on_shutdown = on_shutdown,
    web_app = web_app
)


async def main():
    runner: web.BaseRunner = web.AppRunner(
        app = web_app
    )

    await runner.setup()

    ssl_context: SSLContext = None

    if config["web"]["ssl"]["active"]:
        ssl_context = SSLContext(PROTOCOL_TLSv1_2)

        ssl_context.load_cert_chain(
            certfile = config["web"]["ssl"]["paths"]["fullchain"],
            keyfile = config["web"]["ssl"]["paths"]["privkey"]
        )

    site: web.TCPSite = web.TCPSite(
        runner = runner,
        port = config["web"]["port"],
        ssl_context = ssl_context
    )

    await site.start()

    import asyncio
    await asyncio.Event().wait()


if __name__ == "__main__":
    from asyncio import AbstractEventLoop, new_event_loop, set_event_loop

    loop: AbstractEventLoop = new_event_loop()

    set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
