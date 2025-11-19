# import fast api
import os

from fastapi import FastAPI, HTTPException, Depends

from app.models import User, LoginUser, RegisterUser  # import the user model defined by us

# imports for the MongoDB database connection
from motor.motor_asyncio import AsyncIOMotorClient

# import for fast api lifespan
from contextlib import asynccontextmanager

from typing import List # Supports for type hints

from pydantic import BaseModel # Most widely used data validation library for python

from core.utilies.auth.auth_utilies import hash_password, verify_password, create_jwt_token, get_current_username


# define a lifespan method for fastapi
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the database connection
    await startup_db_client(app)
    yield
    # Close the database connection
    await shutdown_db_client(app)


async def startup_db_client(app):
    app.mongodb_client = AsyncIOMotorClient(
        os.getenv("MONGO_URL"))
    app.mongodb = app.mongodb_client.get_database(os.getenv("DATABASE_NAME"))
    print("MongoDB connected.")


async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("Database disconnected.")


app = FastAPI(lifespan=lifespan)

@app.post("/register", response_model=User)
async def insert_user(user: RegisterUser):
    existing_user = await app.mongodb["users"].find_one({
        "$or": [
            {"email": user.email},
            {"username": user.username}]
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    result = await app.mongodb["users"].insert_one(user_dict)
    inserted_user = await app.mongodb["users"].find_one({"_id": result.inserted_id})
    return inserted_user

@app.post('/login')
async def login(data: LoginUser):
    if data.username:
        user = await app.mongodb["users"].find_one({"username": data.username})
    elif data.email:
        user = await app.mongodb["users"].find_one({"email": data.email})
    else:
        raise HTTPException(status_code=400, detail="Username or email required")
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_jwt_token(data={"sub": user["username"]})
    refresh_token = create_jwt_token(data={"sub": user["username"]}, expires=2000)
    return {"access": access_token,
            "refresh": refresh_token,
            "token_type": "bearer"}

@app.get("/me", response_model=User)
async def read_me(current_username: dict = Depends(get_current_username)):
    user = await app.mongodb["users"].find_one({"username": current_username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/users", response_model=List[User])
async def read_users():
    users = await app.mongodb["users"].find().to_list(None)
    return users


@app.get("/users/{email}", response_model=User)
async def read_user_by_email(email: str):
    user = await app.mongodb["users"].find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user



class UpdateUserDTO(BaseModel):
    other_names: List[str] = None
    age: int = None
    # Include other fields as needed, with defaults to None or use the exclude_unset=True option

@app.put("users/update/{email}", response_model=User)
async def update_user(email: str, user_update: UpdateUserDTO):
    updated_result = await app.mongodb["users"].update_one(
        {"email": email}, {"$set": user_update.dict(exclude_unset=True)})
    if updated_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found or no update needed")
    updated_user = await app.mongodb["users"].find_one({"email": email})
    return updated_user

