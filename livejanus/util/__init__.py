from datetime import datetime
from string import ascii_letters, digits, ascii_lowercase
from random import choices

alphanumeric = digits + ascii_letters


def time_as_utc() -> float:
    return datetime.utcnow().timestamp()


class SocketInvalidDataException(Exception):
    pass


def random_string(source: str = alphanumeric, length: int = 6) -> str:
    return "".join(choices(source, k=length))
