from flask import (
    Blueprint, render_template,
    request, session, redirect,
    url_for, flash
)
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField
from wtforms.validators import InputRequired
import requests

from .utils import require_login, require_logout

auth = Blueprint(__name__, 'auth')


class PasswordResetForm(FlaskForm):
    email = StringField('E-Mail', validators=[InputRequired()])
    recaptcha = RecaptchaField()


@auth.route('/login', methods=['GET', 'POST'])
@require_logout
def login():
    if request.method == 'POST':
        if 'accessToken' in request.get_json() and 'refreshToken' in request.get_json():
            access_token = request.get_json().get('accessToken')
            resp = requests.get(
                f'{request.scheme}://{request.host}{url_for("auth_api")}',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            if resp.status_code == 200:
                session['access_token'] = access_token
                session['refresh_token'] = request.get_json().get('refreshToken')
                return 'Success', 200
            else:
                return 'Access Token is invalid', 401
        else:
            return 'Payload is invalid', 400
    return render_template('login.html')


@auth.route('/logout')
@require_login
def logout():
    # add refresh token to blacklist
    resp = requests.delete(
        f'{request.scheme}://{request.host}{url_for("refresh_api")}/{session["refresh_token"]}'
    )
    if resp.status_code != 200:
        print("Unable to blacklist refresh token!")
    session['refresh_token'] = None
    session['access_token'] = None
    return redirect(url_for('app.views.auth.login'), code=302)


@auth.route('/verify/<string:token>')
def verify(token):
    return requests.put(
        f'{request.scheme}://{request.host}{url_for("verify_mail_api", token=token)}'
    ).json().get('message')


@auth.route('/reset/request', methods=['GET', 'POST'])
def request_password_reset():
    form = PasswordResetForm()
    if request.method == 'POST':
        resp = requests.post(
            f'{request.scheme}://{request.host}{url_for("password_reset_api")}',
            json={
                'email': form.email.data
            }
        )
        if resp.status_code != 200:
            flash('Unknown error', 'danger')
        else:
            return redirect(url_for('app.views.auth.login')), 302
    return render_template('resetPassword.html', form=form)


@auth.route('/reset/confirm/<string:token>')
def confirm_password_reset(token):
    resp = requests.put(
        f'{request.scheme}://{request.host}{url_for("password_reset_api", token=token)}'
    )
    if resp.status_code != 200:
        return f'Error: {resp.json().get("message")}'
    return f"Your new password is <code>{resp.json().get('data').get('password')}</code>", 200
