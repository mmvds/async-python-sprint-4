from typing import List, Optional
from logging import config as logging_config, getLogger
import uuid
import ipaddress
import socket

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import URLItem, ShortURLItem, UsageInfo, User
from core.config import app_settings, PROJECT_HOST, PROJECT_PORT, BLACK_LIST
from db.db import get_session
from core.logger import LOGGING


api_router = APIRouter()
security = HTTPBasic()

logger = getLogger(__name__)
logging_config.dictConfig(LOGGING)

async def check_allowed_ip(request: Request):
    real_ip = socket.gethostbyname(request.client.host)
    logger.debug(f'{real_ip=}')
    ip_address = ipaddress.ip_address(real_ip)
    is_banned = any(ip_address in ipaddress.ip_network(network) for network in BLACK_LIST)
    if is_banned:
        raise HTTPException(status_code=403, detail='Forbidden')

@api_router.post('/register', dependencies=[Depends(check_allowed_ip)])
async def register(username: str, password: str, db: AsyncSession = Depends(get_session)):
    user = User(username=username, password=password)
    db.add(user)
    await db.commit()
    return {'message': 'User registered successfully'}


@api_router.post('/shorten', response_model=List[ShortURLItem], dependencies=[Depends(check_allowed_ip)])
async def shorten_urls(
        urls: List[dict],
        credentials: HTTPBasicCredentials = Depends(security),
        db: AsyncSession = Depends(get_session)
):
    user = await db.execute(User.__table__.select().where(User.username == credentials.username))
    user = user.fetchone()
    if user is None or user['password'] != credentials.password:
        raise HTTPException(status_code=401, detail='Unauthorized')

    result = []
    for url_info in urls:
        original_url = url_info.get('original_url')
        visibility = url_info.get('visibility', 'private')

        if visibility not in ['public', 'private']:
            raise HTTPException(status_code=400, detail='Invalid visibility value')

        short_id = str(uuid.uuid4())[:8]
        short_url = f'http://{PROJECT_HOST}:{PROJECT_PORT}/api/v1/{short_id}'
        db_item = URLItem(
            short_id=short_id,
            original_url=original_url,
            visibility=visibility,
            user_id=user.id
        )
        db.add(db_item)
        await db.commit()
        result.append({
            'short_id': short_id,
            'short_url': short_url,
            'original_url': original_url,
            'visibility': visibility
        })
    return result


@api_router.get('/user/status', dependencies=[Depends(check_allowed_ip)])
async def user_status(credentials: HTTPBasicCredentials = Depends(security), db: AsyncSession = Depends(get_session)):
    user = await db.execute(User.__table__.select().where(User.username == credentials.username))
    user = user.fetchone()
    if user is None or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Unauthorized")

    query = URLItem.__table__.select().where(URLItem.user_id == user.id)
    db_items = await db.execute(query)
    result = []
    for db_item in db_items:
        result.append({
            'short_id': db_item.short_id,
            'short_url': f'http://{PROJECT_HOST}:{PROJECT_PORT}/api/v1/{db_item.short_id}',
            'original_url': db_item.original_url,
            'type': db_item.visibility
        })
    return result

@api_router.get('/ping', dependencies=[Depends(check_allowed_ip)])
async def ping_db(db: AsyncSession = Depends(get_session)):
    try:
        await db.execute('SELECT 1')
        return {'status': 'Database is accessible'}
    except:
        raise HTTPException(status_code=500, detail='Database is not accessible')

@api_router.get('/{short_id}', dependencies=[Depends(check_allowed_ip)])
async def get_original_url(short_id: str, credentials: HTTPBasicCredentials = Depends(security),
                           db: AsyncSession = Depends(get_session)):
    db_item = await db.execute(URLItem.__table__.select().where(URLItem.short_id == short_id))
    db_item = db_item.fetchone()

    if db_item is None:
        raise HTTPException(status_code=404, detail='Short URL not found')

    user = await db.execute(User.__table__.select().where(User.username == credentials.username))
    user = user.fetchone()
    if user is None or (user['password'] != credentials.password and db_item.visibility == "private"):
        raise HTTPException(status_code=401, detail='Unauthorized')

    if db_item['is_deleted']:
        raise HTTPException(status_code=410, detail='Gone')

    if db_item.visibility == 'private' and user.id != db_item.user_id:
        raise HTTPException(status_code=401, detail='Unauthorized')

    return db_item['original_url']

@api_router.delete('/{short_id}', dependencies=[Depends(check_allowed_ip)])
async def delete_shortened_url(short_id: str, credentials: HTTPBasicCredentials = Depends(security),
                               db: AsyncSession = Depends(get_session)):
    user = await db.execute(User.__table__.select().where(User.username == credentials.username))
    user = user.fetchone()
    if user is None or user['password'] != credentials.password:
        raise HTTPException(status_code=401, detail='Unauthorized')

    query = URLItem.__table__.select().where((URLItem.short_id == short_id) & (URLItem.user_id == user.id))
    db_item = await db.execute(query)
    db_item = db_item.fetchone()
    if db_item is None:
        raise HTTPException(status_code=404, detail='Short URL not found')

    delete_query = URLItem.__table__.update().where(URLItem.short_id == short_id).values(is_deleted=True)
    await db.execute(delete_query)
    await db.commit()
    return {'message': 'Short URL has been marked as deleted'}


