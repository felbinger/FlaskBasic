from .utils import create_dummy_user, generate_user_session


def test_unauthorized_index(app, client):
    resp = client.get('/')
    assert resp.status_code == 302


# todo can't work without running api
# backend tries to communicate with api
def test_authorized_index(app, client):
    resp = client.get('/', headers={'Set-Cookie': generate_user_session(app, client)})
    assert resp.status_code == 200
