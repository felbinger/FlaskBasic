from flask import current_app
from flask_mail import Mail
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_gnupg import GnuPG
from hkp4py import KeyServer

db = SQLAlchemy()

keyserver = KeyServer("hkps://pgp.ext.selfnet.de")

gpg = GnuPG()


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


def send_mail(subject, recipient, content, force_gpg=False):
    mail = Mail(current_app)

    # check if the email should be encrypted
    if recipient.gpg_enabled or force_gpg:
        fingerprints = list()

        keys = keyserver.search(f'0x{recipient.gpg_fingerprint}', exact=True) if recipient.gpg_fingerprint else None
        if keys and not keys[0].expired:
            # gpg_fingerprint from db is ok
            gpg.import_keys(keys[0].key)
            fingerprints.append(recipient.gpg_fingerprint)
        else:
            # querying to get keys by email address
            keys = list(filter(lambda k: not k.revoked, keyserver.search(recipient.email)))
            for key in keys:
                fingerprints.append(key.keyid)
                gpg.import_keys(key.key)

        # encrypt the content of the email and replace new lines with html new line to beautify mail
        content = gpg.encrypt(
            data=content,
            recipients=fingerprints,
            always_trust=True,
            sign=True,
            passphrase=current_app.config.get('PGP_PASSPHRASE')
        ).data.decode().replace("\n", "</br>")

    mail.send_message(subject=subject, recipients=[recipient.email], html=content)
