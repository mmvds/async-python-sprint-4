from typing import List
from logging import config as logging_config, getLogger
import uuid
import ipaddress
import socket

from fastapi import HTTPException, Request
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import URLItem, ShortURLItem, User
from core.config import app_settings
from core.logger import LOGGING
from db.db import get_session

logger = getLogger(__name__)

logging_config.dictConfig(LOGGING)


class URLShortenerService:
    async def check_allowed_ip(self, request: Request):
        real_ip = socket.gethostbyname(request.client.host)
        logger.debug(f'{real_ip=}')
        ip_address = ipaddress.ip_address(real_ip)
        is_banned = any(ip_address in ipaddress.ip_network(network) for network in app_settings.black_list)
        if is_banned:
            raise HTTPException(status_code=403, detail='Forbidden')

    async def register(self, username: str, password: str, db: AsyncSession):
        user = User(username=username, password=password)
        db.add(user)
        await db.commit()
        return {'detail': 'User registered successfully'}

    async def shorten_urls(self, urls: List[dict], credentials: HTTPBasicCredentials, db: AsyncSession):
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
            short_url = f'http://{app_settings.project_host}:{app_settings.project_port}/api/v1/{short_id}'
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

    async def user_status(self, credentials: HTTPBasicCredentials, db: AsyncSession):
        user = await db.execute(User.__table__.select().where(User.username == credentials.username))
        user = user.fetchone()
        if user is None or user["password"] != credentials.password:
            raise HTTPException(status_code=401, detail="Unauthorized")

        query = URLItem.__table__.select().where(URLItem.user_id == user.id)
        db_items = await db.execute(query)
        return [
            {
                'short_id': db_item.short_id,
                'short_url': f'http://{app_settings.project_host}:{app_settings.project_port}/api/v1/{db_item.short_id}',
                'original_url': db_item.original_url,
                'type': db_item.visibility,
            }
            for db_item in db_items
        ]

    async def ping_db(self, db: AsyncSession):
        try:
            await db.execute('SELECT 1')
            return {'status': 'Database is accessible'}
        except:
            raise HTTPException(status_code=500, detail='Database is not accessible')

    async def get_original_url(self, short_id: str, credentials: HTTPBasicCredentials, db: AsyncSession):
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

        raise HTTPException(status_code=307, detail='Redirected', headers={'location': db_item['original_url']})

    async def delete_shortened_url(self, short_id: str, credentials: HTTPBasicCredentials, db: AsyncSession):
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
        return {'detail': 'Short URL has been marked as deleted'}