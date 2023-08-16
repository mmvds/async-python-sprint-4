import os
from logging import config as logging_config
from pydantic import BaseSettings, PostgresDsn

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)

PROJECT_NAME = os.getenv('PROJECT_NAME', 'Url Shortener')
PROJECT_HOST = os.getenv('PROJECT_HOST', '127.0.0.1')
PROJECT_PORT = int(os.getenv('PROJECT_PORT', '8080'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASE_DIR, '.env')

BLACK_LIST = [
    # "127.0.0.1/24"
    # "192.168.1.0/24",
    "56.24.15.106",
]

class AppSettings(BaseSettings):
    app_title: str = "Url Shortener App"
    database_dsn: PostgresDsn

    class Config:
        env_file = ENV_FILE_PATH

app_settings = AppSettings()
