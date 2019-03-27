from flask.views import MethodView
from flask import request, current_app, url_for
from flask_mail import Mail
from hashlib import sha512
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature, BadSignature
from string import digits, ascii_letters
from werkzeug.security import generate_password_hash
import random

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

        user = User(**data)
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

        return ResultSchema(
            data=user.jsonify(),
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
            for key, val in data.items():
                if key == 'password':
                    setattr(user, key, sha512(val.encode()).hexdigest())
                else:
                    setattr(user, key, val)
            db.session.commit()
            return ResultSchema(data=user.jsonify()).jsonify()
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
                        errors=['invalid role'],
                        status_code=400
                    ).jsonify()
                else:
                    target.role = role
            elif key == 'password':
                setattr(target, key, generate_password_hash(val, method='sha512'))
            else:
                setattr(target, key, val)
        db.session.commit()
        return ResultSchema(data=target.jsonify()).jsonify()


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
            user.password = generate_password_hash(new_password, method='sha512')
            db.session.commit()

        return ResultErrorSchema(
            message='Password has been updated, you will find it in your inbox!',
            status_code=200
        ).jsonify()
