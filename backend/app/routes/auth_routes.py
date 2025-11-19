from fastapi import APIRouter, HTTPException, Depends
from core.utilies.auth.auth_utilies import pwd_context, verify_password, create_jwt_token, get_current_user, \
    hash_password
from app import db
from app.models import User, LoginUser

auth_router = APIRouter()




@auth_router.post("/register")
async def register_user(user: User):
    existing_user = db["users"].find_one({"email": user.email, "username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    result = db["users"].insert_one(user_dict)
    return {"id": str(result.inserted_id), "message": "User registered successfully"}


@auth_router.post("/login")
async def login(data: LoginUser):
    user = db["users"].find_one({"username": data.username})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_jwt_token(data={"sub": user["username"]})
    refresh_token = create_jwt_token(data={"sub": user["username"]}, expires=2000)
    return {"access": access_token,
            "refresh": refresh_token,
            "token_type": "bearer"}


@auth_router.get("/me")
async def read_me(current_user: dict = Depends(get_current_user)):
    return User(**current_user)