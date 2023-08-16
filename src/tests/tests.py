import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from db.db import get_session
from main import app

TEST_DATABASE_DSN = 'postgresql+asyncpg://postgres:postgres@localhost:5432/test'
tables_created = False

async def override_get_session() -> AsyncSession:
    global tables_created

    engine = create_async_engine(TEST_DATABASE_DSN, echo=True, future=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    if not tables_created:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        tables_created = True

    async with async_session() as session:
        yield session

app.dependency_overrides[get_session] = override_get_session
credentials = ('testuser', 'testpass')
urls = [
                {
                    "original_url": "https://www.example.com",
                    "visibility": "public"
                },
                {
                    "original_url": "https://www.example2.com",
                    "visibility": "private"
                }
            ]
public_id = ''
private_id = ''

@pytest.fixture(scope='session')
def client():
    return TestClient(app)

def test_ping_db(client):
    response = client.get('/api/v1/ping')
    assert response.status_code == 200
    assert response.json() == {'status': 'Database is accessible'}

def test_register_user(client):
    response = client.post('/api/v1/register', params={'username': credentials[0], 'password': credentials[1]})
    assert response.status_code == 200
    assert response.json() == {'detail': 'User registered successfully'}

def test_shorten_urls(client):
    global public_id, private_id

    response = client.post('/api/v1/shorten', json=urls, auth=credentials)
    assert response.status_code == 200
    assert len(response.json()) == 2
    public_id, private_id = response.json()[0]['short_id'], response.json()[1]['short_id']

def test_user_status(client):
    response = client.get('/api/v1/user/status', auth=credentials)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['short_id'] == public_id

def test_get_original_url(client):
    short_id = public_id
    response = client.get(f'/api/v1/{short_id}', auth=credentials)
    assert response.url == urls[0]['original_url']

def test_delete_shortened_url(client):
    short_id = public_id
    response = client.delete(f'/api/v1/{short_id}', auth=credentials)
    assert response.status_code == 200
    assert response.json() == {'detail': 'Short URL has been marked as deleted'}
def test_get_deleted_url(client):
    short_id = public_id
    response = client.get(f'/api/v1/{short_id}', auth=credentials)
    assert response.status_code == 410
    assert response.json() == {'detail': 'Gone'}
