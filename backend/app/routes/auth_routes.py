from datetime import datetime
from app.celery.tasks.email_task import send_welcome_email
from app.models import (ForgotPasswordRequest, ResetPasswordRequest,
                        UsernameRequest, VerifyModel, VerifyRequest)
from app.models.user_models import LoginUser, RegisterUser, User
from core.db.mongo import get_mongodb
from core.services.email_service import send_email
from core.services.template_service import registration_template
from core.utilies.auth.auth_utilies import hash_password, verify_password
from core.utilies.auth.jwt_handlers import create_jwt_token, decode_jwt_token
from core.utilies.auth.verification_handlers import (check_verification_data,
                                                     get_verification_data)
from core.utilies.helpers import my_rand
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

auth_router = APIRouter()


def _make_tokens(username: str, user_id: str | None = None) -> dict[str, str]:
    access = create_jwt_token(
        {"sub": username, "_id": str(user_id) if user_id else None}
    )
    refresh = create_jwt_token(
        {"sub": username, "_id": str(user_id) if user_id else None}, expires=1440
    )
    return {"access": access, "refresh": refresh}


@auth_router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user: RegisterUser, mongodb=Depends(get_mongodb)):
    existing_user = await mongodb["users"].find_one(
        {"$or": [{"email": user.email}, {"username": user.username}]}
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict.setdefault("is_active", False)
    user_dict.setdefault("created_at", datetime.utcnow())

    insert_result = await mongodb["users"].insert_one(user_dict)
    inserted_user = await mongodb["users"].find_one({"_id": insert_result.inserted_id})

    code = my_rand(6)
    ver_data: VerifyModel = get_verification_data(
        inserted_user["username"],
        code,
    )
    await mongodb["verify_codes"].delete_many({"username": inserted_user["username"]})
    await mongodb["verify_codes"].insert_one(ver_data)

    try:
        send_welcome_email.delay(user.email, user.username, code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email: {e}",
        )

    inserted_user.pop("password", None)
    return inserted_user


@auth_router.post("/verify")
async def verify_user(verify: VerifyRequest, mongodb=Depends(get_mongodb)):
    if not verify.username or not verify.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and code are required",
        )

    record = await mongodb["verify_codes"].find_one_and_delete(
        {"username": verify.username}
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found or it expired",
        )

    if not check_verification_data(record, verify.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code"
        )

    await mongodb["users"].update_one(
        {"username": verify.username}, {"$set": {"is_active": True}}
    )

    user = await mongodb["users"].find_one({"username": verify.username})
    tokens = _make_tokens(verify.username, user_id=user.get("_id") if user else None)
    return tokens


@auth_router.post("/resend-code")
async def resend_verification_code(data: UsernameRequest, mongodb=Depends(get_mongodb)):
    username = data.username
    user = await mongodb["users"].find_one({"username": username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already verified"
        )

    code = my_rand(6)
    ver_data: VerifyModel = get_verification_data(username, code)
    await mongodb["verify_codes"].delete_many({"username": username})
    await mongodb["verify_codes"].insert_one(ver_data)
    try:
        send_welcome_email.delay(user.email, user.username, code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )

    return {"message": "Verification code resent"}


@auth_router.post("/forgot-password/request")
async def forgot_password_request(
    req: ForgotPasswordRequest, mongodb=Depends(get_mongodb)
):
    user = await mongodb["users"].find_one({"email": req.email})
    if not user:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "If an account with this email exists, a reset code has been sent."
            },
        )

    code = my_rand(6)
    ver_data: VerifyModel = get_verification_data(user["username"], code)
    await mongodb["verify_codes"].delete_many({"username": user["username"]})
    await mongodb["verify_codes"].insert_one(ver_data)
    template = registration_template(user.name, code)

    try:
        await send_email(req.email, "Password Reset Code", template)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email",
        )

    return {
        "message": "If an account with this email exists, a reset code has been sent."
    }


@auth_router.post("/forgot-password/verify")
async def forgot_password_verify(
    payload: ResetPasswordRequest, mongodb=Depends(get_mongodb)
):
    verify = payload.verify
    if not verify.username or not verify.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and code are required",
        )

    record = await mongodb["verify_codes"].find_one_and_delete(
        {"username": verify.username}
    )
    if not record or not check_verification_data(record, verify.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    hashed_password = hash_password(payload.new_password)
    await mongodb["users"].update_one(
        {"username": verify.username}, {"$set": {"password": hashed_password}}
    )

    return {"message": "Password updated successfully"}


@auth_router.post("/login")
async def login(dto: LoginUser, mongodb=Depends(get_mongodb)):
    user = None
    if getattr(dto, "username", None):
        user = await mongodb["users"].find_one({"username": dto.username})
    elif getattr(dto, "email", None):
        user = await mongodb["users"].find_one({"email": dto.email})

    if not user or not verify_password(dto.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    tokens = _make_tokens(user["username"], user_id=user.get("_id"))
    return tokens


@auth_router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = decode_jwt_token(refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    username = payload.get("sub")
    user_id = payload.get("_id")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    tokens = _make_tokens(username, user_id=user_id)
    return tokens
