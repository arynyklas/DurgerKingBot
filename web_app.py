from aiohttp import web
from aiohttp.web import Request, Response, json_response

from aiogram.types import LabeledPrice
from aiogram.utils.web_app import check_webapp_signature, safe_parse_webapp_init_data
from json import loads
from os import path
from glob import glob
from pathlib import Path

from utils import open_and_mimetype

import aiogram

from typing import List, Callable, Union


PAGE_CONTENTS: dict = {}

work_dir: Path = Path(path.dirname(path.realpath(__file__)))

routes: web.RouteTableDef = web.RouteTableDef()


for filepath in glob("static/**", recursive=True):
    try:
        PAGE_CONTENTS[
            filepath.replace("\\", "/").replace("static/", "")
        ] = open_and_mimetype(
            filepath = filepath
        )

    except (IsADirectoryError, PermissionError, FileNotFoundError):
        continue


async def webapp_error_middleware(request: web.Request, handler: Callable) -> web.Response:
    try:
        return await handler(request)

    except web.HTTPNotFound:
        return web.Response(
            status = 404,
            text = "Not Found"
        )

    except web.HTTPMethodNotAllowed:
        return web.Response(
            status = 405,
            text = "Method Not Allowed"
        )

    except:
        request.app["logger"].exception(
            "Error handling request: from={_from}, path={path}, method={method}, content={content}".format(
                _from = request.remote,
                path = request.rel_url,
                method = request.method,
                content = await request.text()
            )
        )

        return web.Response(
            status = 500,
            text = "Server-side error"
        )


@routes.get("/")
async def index_route(request: Request) -> Response:
    return web.Response(
        status = 200,
        body = PAGE_CONTENTS["index.html"][0],
        headers = {
            "Content-Type": "text/html; charset=utf-8"
        }
    )


@routes.post("/check")
async def check_route(request: Request) -> Response:
    bot: aiogram.Bot = request.app["bot"]

    data = await request.post()

    if check_webapp_signature(bot._token, data["_auth"]):
        return json_response(
            data = {
                "ok": True
            }
        )

    return json_response(
        data = {
            "ok": False,
            "err": "Unauthorized"
        },
        status = 401
    )


@routes.post("/webapp")
async def webapp_route(request: Request) -> Response:
    bot: aiogram.Bot = request.app["bot"]

    data: dict = await request.post()

    try:
        webapp_data = safe_parse_webapp_init_data(
            token = bot._token,
            init_data = data["_auth"],
            _loads = loads
        )

    except ValueError:
        return json_response(
            data = {
                "ok": False,
                "err": "Unauthorized"
            },
            status = 401
        )

    order_data: List[dict] = loads(
        s = data["order_data"]
    )

    food_items: List[dict] = request.app["food_items"]

    invoice_url: str = None

    if data["invoice"] == "1":
        payload: List[str] = []
        prices: List[LabeledPrice] = []

        for order_item in order_data:
            id: int = order_item["id"]
            count: int = order_item["count"]

            payload.append(
                "{id}:{count}".format(
                    id = id,
                    count = count
                )
            )

            food_item: dict = food_items[id]

            prices.append(
                LabeledPrice(
                    label = food_item["name"],
                    amount = int(food_item["price"] * count * 100)
                )
            )

        invoice_url = await bot.create_invoice_link(
            title = "Order",
            description = "order",
            payload = payload,
            provider_token = request.app["bot_provider_token"],
            currency = "USD",
            prices = prices,
            max_tip_amount = 100000,
            suggested_tip_amounts = request.app["suggested_tip_amounts"],
            need_name = True,
            need_phone_number = True,
            need_shipping_address = True
        )

    return json_response(
        data = {
            "ok": True,
            "invoice_url": invoice_url
        },
        status = 200
    )


@routes.get("/static/{path:.*}")
async def static_file_route(request: web.Request) -> web.Response:
    req_path: str = request.match_info.get("path")

    filepath: Path = Path(path.abspath("static/" + req_path))

    if work_dir not in filepath.parents:
        return web.Response(
            status = 403
        )

    if not filepath.exists():
        return web.Response(
            status = 404
        )

    file: Union[bytes, str]
    content_type: str

    file, content_type = PAGE_CONTENTS[req_path]

    return web.Response(
        status = 200,
        body = file,
        headers = {
            "Content-Type": content_type
        }
    )
