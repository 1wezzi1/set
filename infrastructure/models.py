import uuid

from sqlalchemy import Column, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator

from .db import Base


class GUID(TypeDecorator):
    """Кросс-БД UUID: CHAR(36) для SQLite, native UUID для Postgres."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class UserModel(Base):
    __tablename__ = "users"
    id = Column(GUID, primary_key=True)
    name = Column(String, nullable=False)


class DebtModel(Base):
    __tablename__ = "debts"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    debtor_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    creditor_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)

    __table_args__ = (Index("ix_debts_pair", "debtor_id", "creditor_id"),)