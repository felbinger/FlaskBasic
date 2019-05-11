from tests.utils import Utils
import json


def test_index_unauthorized(app, client):
    resp = client.get('/')
    assert resp.status_code == 302


def test_index_authorized(app, client):
    # utils = Utils(app, client)
    # resp = client.get('/', headers={'Set-Cookie': utils.generate_session()})
    # assert resp.status_code == 200
    pass
