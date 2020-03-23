from marshmallow import Schema, fields, validate

from ..schemas import validate_spaces


class DaoCreateUserSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=80), validate_spaces]
    )
    email = fields.Email(
        required=True,
        validate=[validate_spaces]
    )
    password = fields.Str(
        required=True,
        validate=[validate.Length(min=8, max=200)]
    )
    role = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=50)]
    )


class DaoUpdateUserSchema(Schema):
    username = fields.Str(validate=[validate.Length(min=1, max=80)])
    displayName = fields.Str(validate=[validate.Length(min=0, max=128)])
    email = fields.Email([validate_spaces])
    password = fields.Str(validate=[validate.Length(min=8, max=200)])
    role = fields.Str(validate=[validate.Length(min=1, max=50)])
    totp_enabled = fields.Boolean()
    # token to deactivate 2fa
    totp_token = fields.Str(allow_none=True)
    gpg_enabled = fields.Boolean()


class DaoRequestPasswordResetSchema(Schema):
    email = fields.Email([validate_spaces], required=True)
