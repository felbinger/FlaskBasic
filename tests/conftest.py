import pytest
import requests
import json
import werkzeug.wrappers

from app.config import TestingConfig
from app.utils import db as database
from app import create_app


@pytest.fixture
def app():
    # noinspection PyShadowingNames
    app = create_app(TestingConfig)
    return app


# noinspection PyShadowingNames
@pytest.fixture
def client(app):
    with app.app_context():
        database.create_all()
    c = app.test_client()
    setattr(c, 'db', database)
    # Mocking library functions
    requests.post = c.post
    werkzeug.wrappers.BaseResponse.json = lambda self, **kwargs: json.loads(self.data.decode())
    return c
