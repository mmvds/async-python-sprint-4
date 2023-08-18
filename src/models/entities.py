import uuid
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from pydantic import BaseModel

from .base import Base


class URLItem(Base):
    __tablename__ = "urls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_id = Column(String(8), unique=True, index=True)
    original_url = Column(String(512))
    is_deleted = Column(Boolean, default=False)
    visibility = Column(String(16), default="private")
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

class ShortURLItem(BaseModel):
    short_id: str
    short_url: str
    original_url: str
    visibility: str

class UsageInfo(BaseModel):
    timestamp: datetime
    client_info: str

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(32), unique=True, index=True)
    password = Column(String(256))