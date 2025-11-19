from fastapi import FastAPI
from core.mongo import db
app = FastAPI()
from .routes import router
app.include_router(router)

__all__ = ["app", "db"]