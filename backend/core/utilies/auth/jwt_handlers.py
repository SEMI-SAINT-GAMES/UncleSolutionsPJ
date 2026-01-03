import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_jwt_token(data: dict, expires: int | None = None) -> str:
    to_encode = data.copy()
    if expires:
        expire = datetime.utcnow() + timedelta(minutes=expires)
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


def refresh_jwt_token(payload: str) -> str:
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_username(
    token: str = Depends(oauth2_scheme),
) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def create_data_jwt_token(token: str, expires: datetime, type: str) -> dict:
    user_id = get_current_user_id(token)
    data = {"token": token, "type": type, "expire_at": expires, "user_id": user_id}
    return data
