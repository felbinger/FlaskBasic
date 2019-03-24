from flask.views import MethodView
from flask import request

from app.db import db
from ..user import User
from ..authentication import require_token, require_admin
from ..schemas import ResultSchema, ResultErrorSchema
from .models import Role
from .schemas import DaoCreateRoleSchema, DaoUpdateRoleSchema


class RoleResource(MethodView):
    @require_token
    def get(self, name, **_):
        if name is None:
            # get all roles
            return ResultSchema(
                data=[d.jsonify() for d in Role.query.all()]
            ).jsonify()
        else:
            # get a role by the name in the resource (url)
            data = Role.query.filter_by(name=name).first()
            if not data:
                return ResultErrorSchema(
                    message='Role does not exist!',
                    status_code=404
                ).jsonify()
            return ResultSchema(
                data=data.jsonify() or None
            ).jsonify()

    @require_token
    @require_admin
    def post(self, **_):
        data = request.get_json() or {}
        schema = DaoCreateRoleSchema()
        error = schema.validate(data)
        if error:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=error,
                status_code=400
            ).jsonify()
        for role in Role.query.all():
            if data.get('name') == role.name:
                return ResultErrorSchema(
                    message='Name already in use!',
                    status_code=400
                ).jsonify()
        role = Role(
            name=data.get('name'),
            description=data.get('description')
        )
        db.session.add(role)
        db.session.commit()
        return ResultSchema(
            data=role.jsonify(),
            status_code=201
        ).jsonify()

    @require_token
    @require_admin
    def put(self, name, **_):
        data = request.get_json() or {}
        schema = DaoUpdateRoleSchema()
        error = schema.validate(data)
        if error:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=error,
                status_code=400
            ).jsonify()
        role = Role.query.filter_by(name=name).first()
        if not role:
            return ResultErrorSchema(
                message='Role does not exist!',
                status_code=404
            ).jsonify()
        role.description = data.get('description')
        db.session.commit()
        return ResultSchema(
            data=role.jsonify()
        ).jsonify()

    @require_token
    @require_admin
    def delete(self, name, **_):
        if name == 'admin':
            return ResultErrorSchema(
                message='Admin role cannot be deleted!',
                status_code=422
            ).jsonify()
        if name == 'user':
            return ResultErrorSchema(
                message='User role cannot be deleted!',
                status_code=422
            ).jsonify()
        role = Role.query.filter_by(name=name).first()
        if not role:
            return ResultErrorSchema(
                message='Role does not exist!',
                status_code=404
            ).jsonify()
        for user in User.query.all():
            if user.role == role:
                return ResultErrorSchema(
                    message='Role is in use!',
                    status_code=422
                ).jsonify()
        db.session.delete(role)
        db.session.commit()
        return 'Successfully deleted role!', 200
