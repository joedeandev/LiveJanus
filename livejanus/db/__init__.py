from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime
from livejanus.auth import auth_handler
from livejanus.util import random_string, time_as_utc
from typing import Union
from io import StringIO
from csv import writer as csv_writer
from sqlalchemy.engine import Engine
from sqlalchemy import event

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    signup_time = db.Column(db.Float, nullable=False)
    last_authentication = db.Column(db.Float, nullable=False)

    def __init__(self, username: str, password: str, email: str):
        self.username = username
        self.password = auth_handler.hash(password)
        self.email = email
        self.signup_time = datetime.utcnow().timestamp()
        self.last_authentication = self.signup_time

    @classmethod
    def authenticate(cls, username: str, password: str) -> Union[str, bool]:
        response = auth_handler.authenticate(username, password, User)
        if response is not False:
            User.query.filter(
                User.username == username
            ).first().last_authentication = time_as_utc()
            db.session.commit()
        return response


class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    name = db.Column(db.String, nullable=False)
    key = db.Column(db.String, nullable=False, unique=True)
    start_time = db.Column(db.Float, nullable=True)
    end_time = db.Column(db.Float, nullable=True)
    max_value = db.Column(db.Integer, nullable=False)
    is_premium = db.Column(db.Boolean, nullable=False, default=False)
    created_time = db.Column(db.Float, nullable=False)
    lazy_records = db.Column(db.Integer, nullable=False)

    def __init__(
        self,
        owner_id: int,
        name: str,
        start_time: float = None,
        end_time: float = None,
        max_value: int = -1,
        premium: bool = False,
    ):
        self.owner = owner_id
        self.name = name
        self.created_time = time_as_utc()
        self.lazy_records = 0
        self.is_premium = premium
        self.max_value = max_value

        if start_time is not None and end_time is not None:
            if end_time <= start_time:
                raise ValueError(f"Event end ({end_time}) is before start {start_time}")
            self.start_time = start_time
            self.end_time = end_time
        elif start_time is None and end_time is None:
            pass
        elif start_time is None or end_time is None:
            raise ValueError(f"Event end and start must both be None or an integer")

        self.max_value = max_value
        key_length = 8
        while True:
            key = random_string(length=key_length)
            if Event.from_key(key) is not None:
                key_length += 1
                continue
            break
        self.key = key

    @property
    def is_happening(self) -> bool:
        if not self.is_premium:
            return True
        if self.end_time is None:
            return True
        return self.start_time <= time_as_utc() <= self.end_time

    @property
    def is_finished(self) -> bool:
        if not self.is_premium:
            return False
        if self.end_time is None:
            return False
        return time_as_utc() >= self.end_time

    def add_record(self, user_id: int, value: int):
        if value not in [-1, 1]:
            raise ValueError("Invalid value for record")
        if self.is_premium:
            record = Record(user_id, self.id, value)
            db.session.add(record)
        else:
            self.lazy_records += value
        db.session.commit()
        return self.total_value

    @classmethod
    def from_key(cls, key: str) -> "Event":
        return Event.query.filter(Event.key == key).first()

    @property
    def total_value(self) -> int:
        if self.is_premium:
            query = db.session.query(func.sum(Record.value)).filter(
                Record.event == self.id
            )
            if self.start_time is not None:
                query = query.filter(Record.time >= self.start_time)
                query = query.filter(Record.time <= self.end_time)
            try:
                record_total = int(query.all()[0][0])
            except TypeError:
                record_total = 0
            return self.lazy_records + record_total
        return self.lazy_records

    def create_csv(self):
        string_io = StringIO()
        writer = csv_writer(string_io)
        writer.writerow(["Timestamp (UTC)", "Recording User", "Value"])
        if self.lazy_records != 0:
            writer.writerow([0, "Undetailed Records", self.lazy_records])
        user_id_map = {}
        for record in Record.query.filter(Record.event == self.id).order_by(
            Record.time
        ):
            if record.user not in user_id_map:
                eventuser = EventUser.query.filter(EventUser.id == record.user).first()
                if eventuser is None:
                    username = "Unknown"
                else:
                    username = eventuser.username
                user_id_map[record.user] = username
            writer.writerow([int(record.time), user_id_map[record.user], record.value])
        return string_io.getvalue()


class EventUser(db.Model):
    __tablename__ = "eventuser"
    __table_args__ = (db.UniqueConstraint("event", "username", name="_event_username"),)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event = db.Column(
        db.Integer, db.ForeignKey("eventuser.id", ondelete="CASCADE"), nullable=False
    )
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_time = db.Column(db.Float, nullable=False)

    def __init__(self, event_id: int, username: str, password: str):
        self.event = event_id
        self.username = username
        self.set_password(password)
        self.created_time = time_as_utc()

    def set_password(self, password: str):
        self.password = auth_handler.hash(password)

    @classmethod
    def authenticate(
        cls, username: str, password: str, event_id: int
    ) -> Union[str, bool]:
        return auth_handler.authenticate(username, password, EventUser, event_id)


class Record(db.Model):
    __tablename__ = "record"
    __table_args__ = (
        db.Index("_event", "event"),
        db.PrimaryKeyConstraint("user", "time"),
    )
    user = db.Column(
        db.Integer, db.ForeignKey("eventuser.id", ondelete="CASCADE"), nullable=False
    )
    event = db.Column(
        db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    time = db.Column(db.Float, nullable=False)
    value = db.Column(db.SmallInteger, nullable=False)

    def __init__(self, user_id: int, event_id: int, value: int):
        if abs(value) != 1:
            raise ValueError(f"Invalid value {value} given for Record")
        self.time = time_as_utc()
        self.user = user_id
        self.event = event_id
        self.value = value


class StripeSession(db.Model):
    __tablename__ = "stripe"
    user = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    session = db.Column(db.String, nullable=False, unique=True, primary_key=True)
    created = db.Column(db.Integer, nullable=False)
    used = db.Column(db.Boolean, nullable=False)

    def __init__(self, user: int, session: str, token: str):
        self.user = user
        self.session = session
        self.created = int(time_as_utc())
        self.used = False


@event.listens_for(Engine, "connect")
def set_journal_mode(*args):
    cursor = args[0].cursor()
    cursor.execute("PRAGMA journal_mode = MEMORY")
    cursor.close()
