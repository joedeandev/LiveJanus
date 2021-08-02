FROM python:alpine3.13

ADD ./requirements.txt /requirements.txt

RUN apk add g++ gcc musl-dev libffi-dev sqlite && \
    pip install --upgrade cffi pip setuptools  && \
    pip install --no-cache-dir -r /requirements.txt && \
    rm /requirements.txt

COPY . /app

ENV FLASK_APP=/app/app

CMD cd /app && gunicorn --worker-class eventlet --bind 0.0.0.0:8000 --workers 1 app:app
