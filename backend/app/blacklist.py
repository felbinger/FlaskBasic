import os
from flask_redis import FlaskRedis


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


# todo what about testing config? - should be also a setblacklist
blacklist = SetBlacklist() if os.environ.get('FLASK_ENV') == 'development' else RedisBlacklist()
