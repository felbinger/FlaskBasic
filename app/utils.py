from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RedisBlacklist:
    def __init__(self):
        self.blacklist = FlaskRedis()

    def add(self, token):
        self.blacklist.sadd('blacklist', token)
        pass

    def check(self, token):
        return self.blacklist.smembers(token)


class SetBlacklist:
    def __init__(self):
        self.blacklist = set()

    def add(self, token):
        self.blacklist.add(token)

    def check(self, token):
        return token in self.blacklist
