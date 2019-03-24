FROM python:3.6-alpine

ENV MYSQL_HOSTNAME=db
ENV MYSQL_PORT=3306
ENV MYSQL_USERNAME=flaskbasic
ENV MYSQL_DATABASE=flaskbasic

EXPOSE 80

COPY . /app
WORKDIR /app
RUN apk add gcc musl-dev libffi-dev libressl-dev
RUN pip install pipenv
RUN pipenv install
CMD pipenv run prod
