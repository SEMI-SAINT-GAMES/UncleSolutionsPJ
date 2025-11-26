import hashlib
from datetime import datetime, timedelta
from app.models import VerifyModel


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def get_verification_data(username: str, code: str) -> VerifyModel:

    data = {
        "hashcode": hash_code(code),
        "username": username,
        "expire_at": datetime.utcnow() + timedelta(minutes=10),
    }
    return data


def check_verification_data(hash_data: VerifyModel, provided_code: str) -> bool:
    new_hash = hash_code(provided_code)
    print("TRUE>>>", hash_data["hashcode"] == new_hash)
    return (
        hash_data["hashcode"] == hash_code(provided_code)
        and hash_data["expire_at"] > datetime.utcnow()
    )
