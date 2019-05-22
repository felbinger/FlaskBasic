from marshmallow import Schema, fields, validate


class DaoTokenSchema(Schema):
    token = fields.Str(
        required=True,
        validate=[validate.Length(min=6, max=6)]
    )
