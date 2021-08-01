FROM python:alpine3.13

COPY . /app

RUN apk add g++ gcc musl-dev libffi-dev && \
    pip install --upgrade cffi pip setuptools  && \
    pip install --no-cache-dir -r /app/requirements.txt

CMD cd /app && gunicorn --worker-class eventlet --bind 0.0.0.0:8000 --workers 4 app:app
