import os
from logging import config as logging_config
from pydantic import BaseSettings, PostgresDsn

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASE_DIR, '.env')

class AppSettings(BaseSettings):
    app_title: str = "Url Shortener App"
    database_dsn: PostgresDsn
    database_logging: bool = True
    project_name: str = 'Url Shortener'
    project_host: str = '127.0.0.1'
    project_port: int = 8080
    black_list: list = [
        # "127.0.0.1/24"
        # "192.168.1.0/24",
        "56.24.15.106",
    ]

    class Config:
        env_file = ENV_FILE_PATH


app_settings = AppSettings()
