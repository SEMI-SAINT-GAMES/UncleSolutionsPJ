from fastapi import APIRouter, HTTPException, Depends

from app.models import VerifyModel, VerifyRequest, ForgotPasswordRequest, ResetPasswordRequest
from core.db.mongo import get_mongodb
from app.models.user_models import RegisterUser, User, LoginUser
from core.services.email_service import send_email
from core.utilies.auth.auth_utilies import hash_password, verify_password
from core.utilies.auth.jwt_handlers import create_jwt_token, decode_jwt_token
from core.utilies.auth.verification_handlers import get_verification_data, check_verification_data
from core.utilies.helpers import my_rand

auth_router = APIRouter()

@auth_router.get("/r")
async def root():
    r = my_rand(6)
    return {"message": f"Auth service is running. Random number: {r}"}
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
    try:
        result = await mongodb["users"].insert_one(user_dict)
        inserted_user = await mongodb["users"].find_one({"_id": result.inserted_id})
        code = my_rand(6)
        print("code>>>>", code)
        ver_data: VerifyModel = get_verification_data(inserted_user['username'], code)
        verify = await mongodb["verify_codes"].insert_one(ver_data)
        await send_email(user.email, "Welcome to Our Service", f"<h1>Welcome, {user.name}!</h1><p>Thank you for registering, Your code is <b>{code}</b></p>")
        return inserted_user
    except Exception as e:
        await mongodb["users"].delete_one({"_id": result.inserted_id})
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@auth_router.post("/verify")
async def verify_user(verify: VerifyRequest, mongodb = Depends(get_mongodb)):
    try:
        if not verify.username or not verify.code:
            raise HTTPException(400, "Username and code are required")
        hash_data = await mongodb['verify_codes'].find_one_and_delete({"username": verify.username})
        if not check_verification_data(hash_data, verify.code):
            raise HTTPException(400, "Invalid verification code")
        update_result = await mongodb["users"].update_one(
            {"username": verify.username},
            {"$set": {"is_active": True}}
        )
        return {
            "access": create_jwt_token({"sub": verify.username}),
            "refresh": create_jwt_token({"sub": verify.username}, expires=1440)
            }

    except Exception as e:
        await mongodb['verify_codes'].delete_one({"username": verify.username})
        raise HTTPException(500, f"Verification failed: {str(e)}")

@auth_router.post("/resend-code")
async def resend_verification_code(username: str, mongodb = Depends(get_mongodb)):
    user = await mongodb["users"].find_one({"username": username})
    if not user:
        raise HTTPException(404, "User not found")
    if user.get("is_active", True):
        raise HTTPException(400, "User is already verified")
    code = my_rand(6)
    ver_data: VerifyModel = get_verification_data(username, code)
    await mongodb["verify_codes"].delete_many({"username": username})
    await mongodb["verify_codes"].insert_one(ver_data)
    await send_email(user["email"], "Resend Verification Code", f"<p>Your new verification code is <b>{code}</b></p>")
    return {"message": "Verification code resent"}

@auth_router.post("/forgot-password/request")
async def forgot_password_request(forgot_req: ForgotPasswordRequest, mongodb = Depends(get_mongodb)):
    user = await mongodb["users"].find_one({"email": forgot_req.email})
    if not user:
        raise HTTPException(404, "User not found")
    code = my_rand(6)
    ver_data: VerifyModel = get_verification_data(user['username'], code)
    await mongodb["verify_codes"].delete_many({"username": user['username']})
    await mongodb["verify_codes"].insert_one(ver_data)
    await send_email(forgot_req.email, "Password Reset Code", f"<p>Your password reset code is <b>{code}</b></p>")
    return {"message": "Password reset code sent"}
@auth_router.post("/forgot-password/verify")
async def forgot_password_verify(verify_password: ResetPasswordRequest, mongodb = Depends(get_mongodb)):
    try:
        if not verify_password.verify.username or not verify_password.verify.code:
            raise HTTPException(400, "Username and code are required")
        hash_data = await mongodb['verify_codes'].find_one_and_delete({"username":verify_password.verify.username})
        if not check_verification_data(hash_data, verify_password.verify.code):
            raise HTTPException(400, "Invalid verification code")
        hashed_password = hash_password(verify_password.new_password)
        update_result = await mongodb["users"].update_one(
            {"username": verify_password.verify.username},
            {"$set": {"password": hashed_password}}
        )
        return {"message": "Password updated successfully"}
    except Exception as e:
        await mongodb['verify_codes'].delete_one({"username": verify_password.verify.username})
        raise HTTPException(500, f"Password reset failed: {str(e)}")
@auth_router.post("/login")
async def login(dto: LoginUser, mongodb = Depends(get_mongodb)):
    if dto.username:
        user = await mongodb["users"].find_one({"username": dto.username})
    else:
        user = await mongodb["users"].find_one({"email": dto.email})
    if not user.get("is_active", True):
        raise HTTPException(403, "User account is inactive")
    if not user or not verify_password(dto.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")
    access = create_jwt_token({"sub": user["username"], "_id": str(user["_id"])})
    refresh = create_jwt_token({"sub": user["username"],  "_id": str(user["_id"])}, expires=1440)
    return {"access": access, "refresh": refresh}


@auth_router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = decode_jwt_token(refresh_token)
        username = payload.get("sub")
        user_id = payload.get("_id")
        if not username:
            raise HTTPException(401, "Invalid token")
        access = create_jwt_token({"sub": username, "_id": str(user_id)})
        refresh = create_jwt_token({"sub": username, "_id": str(user_id)}, expires=1440)
        return {"access": access, "refresh": refresh}
    except Exception:
        raise HTTPException(401, "Invalid or expired refresh token")