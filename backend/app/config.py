import os


class Config(object):
    DEBUG = False
    MAIL_DEBUG = False
    MAIL_DEFAULT_SENDER = 'flaskbasic@localhost'
    SECRET_KEY = 'os!zj92WqrxgdT66KLJe7BqnhgEEaM4i9h1.kN5MBYW-N42eI06SWB2FF878KiEUYF@V'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TOKEN_VALIDITY = 2  # hours
    QR_SCALE = 5


class ProductionConfig(Config):
    username = os.environ.get('MYSQL_USERNAME')
    password = os.environ.get('MYSQL_PASSWORD')
    hostname = os.environ.get('MYSQL_HOSTNAME')
    port = os.environ.get('MYSQL_PORT') or 3306
    database = os.environ.get('MYSQL_DATABASE')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}?charset=utf8mb4'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT') or 465
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_SENDER')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_USERNAME')
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')

    # encryption method (unencrypted, starttls or ssl)
    enc = os.environ.get('MAIL_ENCRYPTION') or 'unencrypted'
    MAIL_USE_TLS = True if enc == 'starttls' else False
    MAIL_USE_SSL = True if enc == 'ssl' else False


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:root@localhost:9999/flaskbasic?charset=utf8mb4'
    DEBUG = True
    MAIL_DEBUG = True


class TestingConfig(Config):
    TESTING = True
