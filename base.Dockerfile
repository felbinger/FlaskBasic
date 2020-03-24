FROM python:3.7-alpine

WORKDIR /app
COPY requirements.txt /app/
RUN apk add gcc musl-dev libffi-dev libressl-dev gnupg
RUN pip install -r /app/requirements.txt