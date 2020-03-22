from flask import current_app
from flask_mail import Mail
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_gnupg import GnuPG
from hkp4py import KeyServer

db = SQLAlchemy()

# TODO https
keyserver = KeyServer("hkp://pool.sks-keyservers.net")

gpg = GnuPG()


class RedisBlacklist:
    def __init__(self) -> "RedisBlacklist":
        self.blacklist = FlaskRedis()

    def add(self, token: str):
        self.blacklist.sadd('blacklist', token)
        pass

    def check(self, token: str) -> bool:
        return self.blacklist.smembers(token)


class SetBlacklist:
    def __init__(self):
        self.blacklist = set()

    def add(self, token: str):
        self.blacklist.add(token)

    def check(self, token: str) -> bool:
        return token in self.blacklist


def send_mail(subject: str, recipient: "User", content: str, force_gpg: bool=False):
    mail = Mail(current_app)

    # check if the email should be encrypted
    if recipient.gpg_enabled or force_gpg and recipient.gpg_public_key:

        x = gpg.import_keys(recipient.gpg_public_key)

        # encrypt the content of the email and replace new lines with html new line to beautify mail
        content = gpg.encrypt(
            data=content,
            recipients=[recipient.gpg_fingerprint],
            always_trust=True,
            sign=True,
            passphrase=current_app.config.get('PGP_PASSPHRASE')
        ).data.decode().replace("\n", "</br>")

    # TODO content is encrypted, due to wrong mime type the client won't recognise as encrypted email

    mail.send_message(subject=subject, recipients=[recipient.email], html=content)
