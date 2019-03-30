from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length
import requests

from .utils import require_login, require_logout

auth = Blueprint(__name__, 'auth')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=1, max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=200)])
    token = StringField("2FA Token", validators=[Length(max=6)])


class PasswordResetForm(FlaskForm):
    email = StringField('E-Mail', validators=[InputRequired()])
    recaptcha = RecaptchaField()


@auth.route('/login', methods=['GET', 'POST'])
@require_logout
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            resp = requests.post(
                f'{request.scheme}://{request.host}{url_for("auth_api")}',
                json={
                    'username': form.username.data,
                    'password': form.password.data,
                    'token': form.token.data or None
                }
            ).json()
            if resp.get('message') == '2FA required':
                return redirect(url_for('app.views.auth.get_2fa'))
            elif resp.get('token'):
                session['Access-Token'] = resp.get('token')
                return redirect(url_for('app.views.default.index'))
            else:
                flash(resp.get('message'), 'danger')
        else:
            flash('Invalid Credentials!', 'danger')
    return render_template('login.html', form=form)


@require_login
@auth.route('/logout')
def logout():
    # todo contact redis server to make token invalid
    session['Access-Token'] = None
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
    return requests.put(
        f'{request.scheme}://{request.host}{url_for("password_reset_api", token=token)}'
    ).json().get('message')
