import os


class Config(object):
    DEBUG = False
    SECRET_KEY = 'os!zj92WqrxgdT66KLJe7BqnhgEEaM4i9h1.kN5MBYW-N42eI06SWB2FF878KiEUYF@V'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TOKEN_VALIDITY = 2  # hours


class ProductionConfig(Config):
    username = os.environ.get('MYSQL_USERNAME')
    password = os.environ.get('MYSQL_PASSWORD')
    hostname = os.environ.get('MYSQL_HOSTNAME')
    port = os.environ.get('MYSQL_PORT') or 3306
    database = os.environ.get('MYSQL_DATABASE')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}?charset=utf8mb4'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:root@localhost:9999/flaskbasic?charset=utf8mb4'
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
