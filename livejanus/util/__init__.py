from datetime import datetime
from os import environ
from random import choices
from string import ascii_letters, digits

alphanumeric = digits + ascii_letters


def time_as_utc() -> float:
    return datetime.utcnow().timestamp()


class SocketInvalidDataException(Exception):
    pass


def random_string(source: str = alphanumeric, length: int = 6) -> str:
    return "".join(choices(source, k=length))


def is_debug() -> bool:
    return environ.get("DEBUG", False).lower() == "true"
