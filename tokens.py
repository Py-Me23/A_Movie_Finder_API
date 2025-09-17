import jwt
import os
from dotenv import load_dotenv
from pydantic import BaseModel


class UserInfo(BaseModel):
    id: str
    email: str
    name: str


def signin_token(payload: dict):
    token = jwt.encode(
        payload, os.getenv("JWT_SECRET_KEY"), algorithm=os.getenv("JWT_ALOGARITHMN")
    )
    return token


def decode_jwt(token: str):
    return jwt.decode(
        token, os.getenv("JWT_SECRET_KEY"), algorithms=[os.getenv("JWT_ALOGARITHMN")]
    )


def create_access_token(data: UserInfo):
    access_token_expires = 60 * 30  # 30 minutes
    refresh_token_expires = 60 * 60 * 24 * 7  # minutes

    access_payload = data.model_dump()
    access_payload["id"] = str(access_payload["id"])
    access_payload.update({"expires": access_token_expires, "type": "access"})
    access_token = signin_token(access_payload)

    refresh_payload = {
        "sub": data.id,
        "expires": refresh_token_expires,
        "type": "refresh",
    }

    refresh_token = signin_token(refresh_payload)
    return {"access_token": access_token, "refresh_token": refresh_token}
