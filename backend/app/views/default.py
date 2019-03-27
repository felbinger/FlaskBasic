from flask import Blueprint, render_template, request, session, url_for
import requests

from .utils import require_login

default = Blueprint(__name__, 'default')


@default.route('/')
@require_login
def index():
    role = requests.get(
        f'{request.scheme}://{request.host}{url_for("auth_api")}',
        headers={'Access-Token': session.get('Access-Token')},
    ).json().get('data').get('role').get('name')
    return render_template('index.html', role=role)

