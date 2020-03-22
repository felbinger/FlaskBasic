from sqlalchemy import Column, String, Integer

from app.utils import db


class Role(db.Model):
    __table_args__ = ({'mysql_character_set': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_520_ci'})
    id: int = Column('id', Integer, primary_key=True)
    name: str = Column('name', String(80), unique=True, nullable=False)
    description: str = Column('description', String(80), nullable=False)

    def jsonify(self) -> dict:
        return {
            'name': self.name,
            'description': self.description
        }
