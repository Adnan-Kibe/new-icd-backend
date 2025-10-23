from datetime import datetime, timedelta
import os

from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import BaseModel
from database import get_session
from fastapi import Depends, HTTPException, status
from typing import Annotated, Literal
from sqlalchemy.orm import Session
from schemas.users_schema import UserSchema
from services.logger import logger
import random
import string


ALGORITHM = os.getenv("ALGORITHM")
ACCESS_SECRET_KEY = os.getenv("ACCESS_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")

db_dependency = Annotated[Session, Depends(get_session)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def otp_generator():
    return ''.join(random.choices(string.digits, k=6))

def generate_jwt_token(data: BaseModel, token_type: Literal["access", "refresh"] = "access") -> str:
    data_to_encode = data.model_dump()

    if token_type == "access":
        expire_delta = datetime.now() + timedelta(minutes=15)
        data_to_encode.update({"exp": expire_delta, "token_type": "access"})
        encoded_jwt = jwt.encode(data_to_encode, ACCESS_SECRET_KEY, algorithm=ALGORITHM)
    else:
        expire_delta = datetime.now() + timedelta(days=1)
        data_to_encode.update({"exp": expire_delta, "token_type": "refresh"})
        encoded_jwt = jwt.encode(data_to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def decode_jwt_token(token: str, model: type[BaseModel], token_type: Literal["access", "refresh"] = "access") -> BaseModel:
    try:
        # Choose secret key based on token type
        secret_key = ACCESS_SECRET_KEY if token_type == "access" else REFRESH_SECRET_KEY
        
        # Decode the token
        decoded_data = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        
        # Validate token type
        if decoded_data.get("token_type") != token_type:
            raise jwt.InvalidTokenError("Invalid token type")
        
        # Check token expiry
        exp = decoded_data.get("exp")
        if not exp:
            raise jwt.InvalidTokenError("Token has no expiry")
        
        # Handle both timestamp and datetime exp formats
        exp_datetime = datetime.fromtimestamp(exp) if isinstance(exp, (int, float)) else exp
        if exp_datetime < datetime.now():
            raise jwt.ExpiredSignatureError("Token has expired")
        
        return model.model_validate(decoded_data)
    
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(str(e))
    except Exception as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
    
def get_current_user(model: type[BaseModel]):
    async def dependency(token: str = Depends(oauth2_scheme)):
        try:
            return decode_jwt_token(token, model)
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

    return dependency

user_dependency = Annotated[UserSchema, Depends(get_current_user(UserSchema))]