from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from datetime import datetime
from pydantic import BaseModel

from .base import Base


class URLItem(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    short_id = Column(String, unique=True, index=True)
    original_url = Column(String)
    is_deleted = Column(Boolean, default=False)
    visibility = Column(String, default="private")
    user_id = Column(Integer, ForeignKey('users.id'))

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

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)