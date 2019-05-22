FROM python:3.7-alpine

ENV MYSQL_HOSTNAME=db
ENV MYSQL_PORT=3306
ENV MYSQL_USERNAME=flaskbasic
ENV MYSQL_DATABASE=flaskbasic
ENV REDIS_HOSTNAME=redis
ENV REDIS_PORT=6379
ENV REDIS_DATABASE=0

EXPOSE 80

COPY . /app
WORKDIR /app
RUN apk add gcc musl-dev libffi-dev libressl-dev gnupg
RUN pip install -r requirements.txt

CMD ["gunicorn", "--workers", "4", "wsgi:application", "--bind", "0.0.0.0:80", "--log-syslog", "--log-level", "DEBUG"]
