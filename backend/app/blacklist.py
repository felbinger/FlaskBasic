import os
from flask_redis import FlaskRedis


class RedisBlacklist:
    def __init__(self):
        self.conn = FlaskRedis()

    def add(self, token):
        self.conn.sadd('blacklist', token)
        pass

    def check(self, token):
        return self.conn.smembers(token)


class SetBlacklist:
    def __init__(self):
        self.data = set()

    def add(self, token):
        self.data.add(token)

    def check(self, token):
        return token in self.data


blacklist = RedisBlacklist() if os.environ.get('FLASK_ENV') == 'productive' else SetBlacklist()
