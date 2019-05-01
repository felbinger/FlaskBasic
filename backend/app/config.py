import os


class Config(object):
    DEBUG = False
    MAIL_DEBUG = False
    MAIL_DEFAULT_SENDER = 'flaskbasic@localhost'
    SECRET_KEY = 'os!zj92WqrxgdT66KLJe7BqnhgEEaM4i9h1.kN5MBYW-N42eI06SWB2FF878KiEUYF@V'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    ACCESS_TOKEN_VALIDITY = 15  # minutes
    REFRESH_TOKEN_VALIDITY = 360  # minutes
    QR_SCALE = 5
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ProductionConfig(Config):
    username = os.environ.get('MYSQL_USERNAME')
    password = os.environ.get('MYSQL_PASSWORD')
    hostname = os.environ.get('MYSQL_HOSTNAME')
    port = os.environ.get('MYSQL_PORT') or 3306
    database = os.environ.get('MYSQL_DATABASE')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}?charset=utf8mb4'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT') or 465
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_SENDER') or 'flaskbasic@localhost'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_USERNAME')
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')

    # encryption method (unencrypted, starttls or ssl)
    enc = os.environ.get('MAIL_ENCRYPTION') or 'unencrypted'
    MAIL_USE_TLS = enc == 'starttls'
    MAIL_USE_SSL = enc == 'ssl'

    # redis configuration to blacklist refresh tokens
    redis_host = os.environ.get('REDIS_HOSTNAME')
    redis_port = os.environ.get('REDIS_PORT') or 6379
    redis_password = os.environ.get('REDIS_PASSWORD') or ''
    redis_db = os.environ.get('REDIS_DATABASE')
    redis_base = f'{redis_host}:{redis_port}/{redis_db}'
    REDIS_URL = f'redis://:{redis_password}@{redis_base}' if redis_password else f'redis://{redis_base}'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:root@localhost:9999/flaskbasic?charset=utf8mb4'
    DEBUG = True
    MAIL_DEBUG = True


class TestingConfig(Config):
    TESTING = True
