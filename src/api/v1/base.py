from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import URLItem, ShortURLItem, UsageInfo, User
from services.services import URLShortenerService
from db.db import get_session

api_router = APIRouter()
security = HTTPBasic()

url_shortener_service = URLShortenerService()

@api_router.post('/register', dependencies=[Depends(url_shortener_service.check_allowed_ip)])
async def register(username: str, password: str, db: AsyncSession = Depends(get_session)):
    return await url_shortener_service.register(username, password, db)

@api_router.post('/shorten', response_model=List[ShortURLItem], dependencies=[Depends(url_shortener_service.check_allowed_ip)])
async def shorten_urls(
        urls: List[dict],
        credentials: HTTPBasicCredentials = Depends(security),
        db: AsyncSession = Depends(get_session)
):
    return await url_shortener_service.shorten_urls(urls, credentials, db)

@api_router.get('/user/status', dependencies=[Depends(url_shortener_service.check_allowed_ip)])
async def user_status(credentials: HTTPBasicCredentials = Depends(security), db: AsyncSession = Depends(get_session)):
    return await url_shortener_service.user_status(credentials, db)

@api_router.get('/ping', dependencies=[Depends(url_shortener_service.check_allowed_ip)])
async def ping_db(db: AsyncSession = Depends(get_session)):
    return await url_shortener_service.ping_db(db)

@api_router.get('/{short_id}', dependencies=[Depends(url_shortener_service.check_allowed_ip)])
async def get_original_url(short_id: str, credentials: HTTPBasicCredentials = Depends(security), db: AsyncSession = Depends(get_session)):
    return await url_shortener_service.get_original_url(short_id, credentials, db)

@api_router.delete('/{short_id}', dependencies=[Depends(url_shortener_service.check_allowed_ip)])
async def delete_shortened_url(short_id: str, credentials: HTTPBasicCredentials = Depends(security), db: AsyncSession = Depends(get_session)):
    return await url_shortener_service.delete_shortened_url(short_id, credentials, db)