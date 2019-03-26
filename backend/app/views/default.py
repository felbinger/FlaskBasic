from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired
import requests

from .utils import require_login, require_logout

default = Blueprint(__name__, 'default')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


@default.route('/')
@require_login
def index():
    role = requests.get(
        f'{request.scheme}://{request.host}{url_for("auth_api")}',
        headers={'Access-Token': session.get('Access-Token')},
    ).json().get('data').get('role').get('name')
    return render_template('index.html', role=role)


@default.route('/login', methods=['GET', 'POST'])
@require_logout
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            resp = requests.post(
                f'{request.scheme}://{request.host}{url_for("auth_api")}',
                json={
                    'username': form.username.data,
                    'password': form.password.data
                }
            ).json()
            if resp.get('token'):
                session['Access-Token'] = resp.get('token')
                return redirect(url_for('app.views.default.index'))
            else:
                flash(resp.get('message'), 'danger')
        else:
            flash('Missing credentials')
    return render_template('login.html', form=form)


@require_login
@default.route('/logout')
def logout():
    # todo contact redis server to make token invalid
    session['Access-Token'] = None
    return redirect(url_for('app.views.default.login'), code=302)


@default.route('/verify/<token>')
def verify(token):
    return requests.put(
        f'{request.scheme}://{request.host}{url_for("verify_mail_api", token=token)}'
    ).json().get('message')
