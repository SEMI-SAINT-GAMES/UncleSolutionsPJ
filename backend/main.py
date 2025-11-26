from dotenv import load_dotenv
from fastapi import FastAPI

from core.db.db_init import lifespan
from app.routes.auth_routes import auth_router
from app.routes.user_routes import user_router
from app.routes.article_routes import article_router
from core.db.mongo import get_mongodb
from core.db.mongo import connect_to_mongo, close_mongo
load_dotenv()
app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])

app.include_router(article_router, prefix="/articles", tags=["Articles"])
@app.on_event("startup")
async def startup_event():
     await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
     await close_mongo()

