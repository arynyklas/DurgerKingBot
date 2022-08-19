from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


class Keyboards:
    def __init__(self, texts: dict, web_app_url: str) -> None:
        self._texts: dict = texts

        self.order: InlineKeyboardMarkup = InlineKeyboardMarkup()

        self.order.add(
            InlineKeyboardButton(
                text = self._texts["order"],
                web_app = WebAppInfo(
                    url = web_app_url
                )
            )
        )
