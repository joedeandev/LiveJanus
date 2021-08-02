from os import environ
from time import time
from typing import Union

from argon2 import PasswordHasher

from livejanus.util import is_debug, random_string


class AuthHandler:
    def __init__(self):
        self._password_hasher = PasswordHasher()
        self._salt = environ.get("HASH_SALT", "saltysalt")
        self._tokens = {}
        self._expire_time = 60 * 60 * 24 * 7
        self._max_tokens = 2 ** 13
        self._socket_ids = {}

    def salt(self, password: str):
        return f"{password}{self._salt}"

    def hash(self, password: str) -> str:
        return self._password_hasher.hash(self.salt(password))

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return self._password_hasher.verify(hashed, self.salt(password))
        except:
            return False

    def authenticate(
        self, username: str, password: str, query_class: type, event_id: int = None
    ) -> Union[str, bool]:
        if event_id is not None:
            user = (
                query_class.query.filter(query_class.event == event_id)
                .filter(query_class.username == username)
                .first()
            )
        else:
            user = query_class.query.filter(query_class.username == username).first()
        if user is None:
            return False
        if is_debug() and password == environ.get("DEBUG_MASTER_PASSWORD", -1):
            result = True
        else:
            result = auth_handler.verify(password, user.password)
        if result:
            token = random_string(length=128)
            expiry = time() + self._expire_time
            if token in self._tokens:
                return self.authenticate(username, password, query_class)
            self._tokens[token] = (user.id, query_class, expiry)
            self._clean_tokens()
            return token
        return False

    def validate(self, token: str):
        if token not in self._tokens:
            return None
        user_id, query_class, expiry = self._tokens[token]
        if self._is_expired(token):
            del self._tokens[token]
            return None
        return query_class.query.filter(query_class.id == user_id).first()

    def _is_expired(self, token: str):
        user_id, query_class, expiry = self._tokens[token]
        return time() > expiry

    def _clean_tokens(self):
        if len(self._tokens) < self._max_tokens:
            return
        queue = set()
        for token in self._tokens.keys():
            if self._is_expired(token):
                queue.add(token)
        for token in queue:
            del self._tokens[token]


class SocketSessionHandler:
    def __init__(self):
        self._data = {}
        self._expire_time = 60 * 60 * 24 * 7

    def save(
        self,
        session_id: str,
        event_user_name: str,
        event_user_id: int,
        event_key: str,
        event_id: int,
    ):
        self._data[session_id] = (
            event_user_name,
            event_user_id,
            event_key,
            event_id,
            time(),
        )
        expired_session_ids = set()
        for session_id in self._data.keys():
            if time() - self._data[session_id][-1] > self._expire_time:
                expired_session_ids.add(session_id)
        for session_id in expired_session_ids:
            del self._data[session_id]

    def fetch(self, session_id: str) -> Union[None, tuple[str, int, str, int]]:
        if session_id not in self._data:
            return None
        return self._data[session_id][:-1]


auth_handler = AuthHandler()
socket_session_handler = SocketSessionHandler()
