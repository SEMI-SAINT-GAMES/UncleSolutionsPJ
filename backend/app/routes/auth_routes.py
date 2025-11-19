from fastapi import APIRouter, HTTPException, Depends
from core.db.mongo import get_mongodb
from app.models.user_models import RegisterUser, User, LoginUser
from core.utilies.auth.auth_utilies import hash_password, verify_password
from core.utilies.auth.jwt_handlers import create_jwt_token, decode_jwt_token
auth_router = APIRouter()
@auth_router.post("/register", response_model=User)
async def register_user(user: RegisterUser, mongodb = Depends(get_mongodb)):
    existing_user = await mongodb["users"].find_one({
        "$or": [
            {"email": user.email},
            {"username": user.username}]
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    result = await mongodb["users"].insert_one(user_dict)
    inserted_user = await mongodb["users"].find_one({"_id": result.inserted_id})
    return inserted_user


@auth_router.post("/login")
async def login(dto: LoginUser, mongodb = Depends(get_mongodb)):
    if dto.username:
        user = await mongodb["users"].find_one({"username": dto.username})
    else:
        user = await mongodb["users"].find_one({"email": dto.email})
    if not user or not verify_password(dto.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")
    access = create_jwt_token({"sub": user["username"]})
    return {"access": access}


@auth_router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = decode_jwt_token(refresh_token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(401, "Invalid token")
        # створюємо новий access token
        new_access = create_jwt_token({"sub": username}, expires_in=900)
        return {"access_token": new_access, "token_type": "bearer"}
    except Exception:
        raise HTTPException(401, "Invalid or expired refresh token")