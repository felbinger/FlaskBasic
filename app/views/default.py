from flask import (
    Blueprint, render_template,
    request, session, url_for,
    send_from_directory, current_app
)
from dateutil.parser import parse
import requests

from .utils import require_login

default = Blueprint(__name__, 'default')


@default.route('/')
@require_login
def index():
    role = requests.get(
        f'{request.scheme}://{request.host}{url_for("auth_api")}',
        headers={'Authorization': f'Bearer {session.get("access_token")}'},
    ).json().get('data').get('role').get('name')
    return render_template('index.html', role=role)


@default.route('/profile', methods=['GET', 'POST'])
@require_login
def profile():
    data = requests.get(
        f'{request.scheme}://{request.host}{url_for("auth_api")}',
        headers={'Authorization': f'Bearer {session.get("access_token")}'},
    ).json().get('data')
    # reformat timestamps
    data['lastLogin'] = parse(data['lastLogin']).strftime(current_app.config['TIME_FORMAT'])
    data['created'] = parse(data['created']).strftime(current_app.config['TIME_FORMAT'])
    return render_template('profile.html', data=data, role=data.get('role').get('name'))


@default.route('/profile/2fa', methods=['GET'])
@require_login
def enable2fa():
    return render_template('setup2FA.html'), {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


@default.route('/enableGPG/<string:token>')
def enable_mail_encryption(token):
    resp = requests.put(
        f'{request.scheme}://{request.host}{url_for("gpg_api")}/{token}'
    )
    if resp.status_code != 200:
        return f'Error: {resp.json().get("message")}'
    return f"Success"
