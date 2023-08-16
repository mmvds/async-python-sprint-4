import logging

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from core.logger import LOGGING
from api.v1 import base
from core.config import app_settings, PROJECT_HOST, PROJECT_PORT


app = FastAPI(
    title=app_settings.app_title,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)

app.include_router(base.api_router, prefix="/api/v1")

if __name__ == '__main__':
    uvicorn.run("main:app", host=PROJECT_HOST, port=PROJECT_PORT)
