from flask.views import MethodView
from flask import request, current_app, url_for
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature, BadSignature
from string import digits, ascii_letters
from io import BytesIO
import random
import pyqrcode

from app.db import db
from ..schemas import ResultSchema, ResultErrorSchema
from ..authentication import require_token, require_admin
from ..role import Role
from ..user.models import User
from .schemas import DaoCreateUserSchema, DaoUpdateUserSchema, DaoRequestPasswordResetSchema


def random_string(length=16):
    return ''.join(random.choice(ascii_letters + digits) for i in range(length))


class UserResource(MethodView):
    @require_token
    @require_admin
    def get(self, uuid, **_):
        if uuid is None:
            return ResultSchema(
                data=[d.jsonify() for d in User.query.all()]
            ).jsonify()
        else:
            data = User.query.filter_by(public_id=uuid).first()
            if not data:
                return ResultErrorSchema(
                    message='User does not exist!',
                    status_code=404
                ).jsonify()
            return ResultSchema(
                data=data.jsonify()
            ).jsonify()

    @require_token
    @require_admin
    def post(self, **_):
        data = request.get_json() or {}
        schema = DaoCreateUserSchema()
        data, error = schema.load(data)
        if error:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=error,
                status_code=400
            ).jsonify()
        user_exists = User.query.filter_by(username=data['username']).first()
        if user_exists:
            return ResultErrorSchema(
                message='Username already in use!',
                status_code=422
            ).jsonify()
        data['role'] = Role.query.filter_by(name=data.get('role')).first()
        if not data['role']:
            return ResultErrorSchema(
                message='Role does not exist!',
                status_code=404
            ).jsonify()

        _enable_2fa = False
        _2fa_secret = None
        if '2fa' in data:
            _enable_2fa = True
            del data['2fa']

        user = User(**data)

        if _enable_2fa:
            _2fa_secret = user.enable_2fa()

        db.session.add(user)
        db.session.commit()

        # generate token to verify email
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(data['email'], salt='verify-email')

        # send email
        mail = Mail(current_app)
        verification_link = f'{request.scheme}://{request.host}{url_for("app.views.auth.verify", token=token)}'
        body = f'Hello, please click <a href="{verification_link}">here</a> to confirm your email.'
        mail.send_message("Verify your email!", recipients=[data['email']], html=body)

        data = user.jsonify()
        data['2fa_secret'] = _2fa_secret

        return ResultSchema(
            data=data,
            status_code=201
        ).jsonify()

    @require_token
    def put(self, uuid, user, **_):
        if uuid == 'me':
            schema = DaoUpdateUserSchema()
            data = request.get_json()
            data, error = schema.load(data)
            if error:
                return ResultErrorSchema(
                    message='Payload is invalid',
                    errors=error,
                    status_code=400
                ).jsonify()
            if 'role' in data.keys():
                return ResultErrorSchema(
                    message='You are not allowed to change your role!',
                    status_code=403
                ).jsonify()
            _2fa_secret = None
            for key, val in data.items():
                if key == 'enable_2fa':
                    if val:
                        _2fa_secret = user.enable_2fa()
                    else:
                        user.disable_2fa()
                else:
                    setattr(user, key, val)
            db.session.commit()
            data = user.jsonify()
            if _2fa_secret:
                data['2fa_secret'] = _2fa_secret
            return ResultSchema(data=data).jsonify()
        else:
            target = User.query.filter_by(public_id=uuid).first()
            if not target:
                return ResultErrorSchema(
                    message='User does not exist',
                    status_code=404
                ).jsonify()
            return require_admin(self._update_user_as_admin)(user=user, target=target)

    @require_token
    @require_admin
    def delete(self, uuid, **_):
        user = User.query.filter_by(public_id=uuid).first()
        db.session.delete(user)
        db.session.commit()
        return ResultSchema(
            data='Successfully deleted user!',
            status_code=200
        ).jsonify()

    def _update_user_as_admin(self, target, **_):
        schema = DaoUpdateUserSchema()
        data = request.get_json()
        data, error = schema.load(data)
        if error:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=error,
                status_code=400
            ).jsonify()
        for key, val in data.items():
            if key == 'role':
                role = Role.query.filter_by(name=val).first()
                if not role:
                    return ResultErrorSchema(
                        message='Invalid Role',
                        status_code=400
                    ).jsonify()
                else:
                    target.role = role
            elif key == 'enable_2fa':
                if not val:
                    target.disable_2fa()
                else:
                    return ResultErrorSchema(
                        message='You are not allowed to enable 2FA.'
                    ).jsonify()
            else:
                setattr(target, key, val)
        db.session.commit()
        data = target.jsonify()
        return ResultSchema(data=data).jsonify()


class VerificationResource(MethodView):
    def put(self, token):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='verify-email', max_age=7200)
        except (BadSignature, SignatureExpired, BadTimeSignature):
            return ResultErrorSchema(
                message='Token is invalid!'
            ).jsonify()
        user = User.query.filter_by(email=email).first()
        user.verified = True
        db.session.commit()
        return ResultErrorSchema(
            message='E-Mail verified successfully!',
            status_code=200
        ).jsonify()


class ResetResource(MethodView):
    def post(self):
        schema = DaoRequestPasswordResetSchema()
        data = request.get_json()
        data, error = schema.load(data)
        if error:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=error,
                status_code=400
            ).jsonify()

        # generate token to reset password
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(data['email'], salt='reset-password')

        user = User.query.filter_by(email=data['email']).first()
        if user:
            # send email
            mail = Mail(current_app)
            link = f'{request.scheme}://{request.host}{url_for("app.views.auth.confirm_password_reset", token=token)}'
            body = f'Hello, if you want to reset your password, click <a href="{link}">here</a>.\n' + \
                   f'If you haven\'t requested a password reset, just ignore this message.'
            mail.send_message("Password Reset!", recipients=[data['email']], html=body)

            print(body)

        return ResultErrorSchema(
            message='Request has been send. Check your inbox!',
            status_code=200
        ).jsonify()

    def put(self, token):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='reset-password', max_age=7200)
        except (BadSignature, SignatureExpired, BadTimeSignature):
            return ResultErrorSchema(
                message='Token is invalid!'
            ).jsonify()

        user = User.query.filter_by(email=email).first()
        if user:
            new_password = random_string()

            # send email
            mail = Mail(current_app)
            body = f'Hello, your new password is: <code>{new_password}</code>'
            mail.send_message("Password Reset!", recipients=[user.email], html=body)

            print(body)

            # update password
            user.password = new_password
            db.session.commit()

        return ResultErrorSchema(
            message='Password has been updated, you will find it in your inbox!',
            status_code=200
        ).jsonify()


class TwoFAResource(MethodView):
    @require_token
    def get(self, user):
        if user.is_2fa_enabled() and not user.code_viewed:
            user.code_viewed = True
            db.session.commit()
            url = pyqrcode.create(user.get_totp_uri())
            stream = BytesIO()
            url.svg(stream, scale=current_app.config['QR_SCALE'])
            return stream.getvalue(), 200, {
                'Content-Type': 'image/svg+xml',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        return ResultErrorSchema(message='Unable to generate QR Code').jsonify()
