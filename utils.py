from json import load, dump

import logging

from typing import Optional, Tuple


_log_format: str = "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"

MIMETYPE_HEADERS: dict = {
    "html": "text/html; charset=utf-8",
    "js": "application/javascript; charset=utf-8",
    "css": "text/css; charset=utf-8",
    "json": "application/json"
}


def get_file_handler() -> logging.Handler:
    file_handler: logging.Handler = logging.FileHandler("log.log")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(_log_format))
    return file_handler

def get_stream_handler() -> logging.Handler:
    stream_handler: logging.Handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler

def get_logger(name: Optional[str]=None) -> logging.Logger:
    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(get_file_handler())
    logger.addHandler(get_stream_handler())
    return logger


def get_config(filename: str) -> dict:
    with open(filename, "r", encoding="utf-8") as file:
        return load(
            fp = file
        )


def save_config(filename: str, data: dict) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        dump(
            obj = data,
            fp = file,
            ensure_ascii = False,
            indent = 4
        )


def open_and_mimetype(filepath: str) -> Tuple[bytes, str]:
    with open(filepath, "rb") as file:
        result: bytes = file.read()

    return result, MIMETYPE_HEADERS.get(
        filepath.split(".")[-1],
        "application/octet-stream"
    )
