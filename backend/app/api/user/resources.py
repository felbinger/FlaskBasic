from flask.views import MethodView
from flask import request
from hashlib import sha512

from app.db import db
from ..schemas import ResultSchema, ResultErrorSchema
from ..authentication import require_token, require_admin
from ..role import Role
from ..user.models import User
from .schemas import DaoCreateUserSchema, DaoUpdateUserSchema


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
        result = schema.load(data)
        if result.errors:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=result.errors,
                status_code=400
            ).jsonify()
        data = result.data
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
                setattr(target, key, sha512(val.encode()).hexdigest())
            else:
                setattr(target, key, val)
        db.session.commit()
        return ResultSchema(data=target.jsonify()).jsonify()
