ARG BASE_IMG=flaskbasic_base
FROM ${BASE_IMG}

ENV MYSQL_HOSTNAME=db
ENV MYSQL_PORT=3306
ENV MYSQL_USERNAME=flaskbasic
ENV MYSQL_DATABASE=flaskbasic
ENV REDIS_HOSTNAME=redis
ENV REDIS_PORT=6379
ENV REDIS_DATABASE=0

EXPOSE 80
WORKDIR /app
COPY . /app


CMD ["gunicorn", "--config", "wsgi_config.py", "wsgi:application"]
