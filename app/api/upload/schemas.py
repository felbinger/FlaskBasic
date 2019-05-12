from marshmallow import Schema, fields


class DaoUploadSchema(Schema):
    file = fields.Str(
        required=True
    )
