from datetime import datetime, timedelta
import os

from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import BaseModel
from database import get_session
from fastapi import Depends
from typing import Annotated, Literal
from sqlalchemy.orm import Session
from logger import logger
import random
import string

from models import Admin, Hospital, User

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
    
USERS = [
    {'work_id': 'EMP-22F3B1E4', 'first_name': 'John', 'last_name': 'Smith', 'email': 'john.smith@example.com', 'occupation': 'Doctor', 'department': 'Cardiology', 'hospital_id': 'HOSP-38A2E9A1'},
    {'work_id': 'EMP-5F7D82C9', 'first_name': 'Mary', 'last_name': 'Johnson', 'email': 'mary.johnson@example.com', 'occupation': 'Nurse', 'department': 'Emergency', 'hospital_id': 'HOSP-A8C9F421'},
]
HOSPITALS = [
    {'hospital_id': 'HOSP-38A2E9A1', 'name': 'Boston General Hospital', 'email': 'contact@bostongeneralhospital.com', 'phone_number': '(555) 123-4567', 'location': '21 Main St, Boston, MA'},
    {'hospital_id': 'HOSP-A8C9F421', 'name': 'Denver General Hospital', 'email': 'contact@denvergeneralhospital.com', 'phone_number': '(555) 678-1234', 'location': '44 Elm St, Denver, CO'},
]
ADMINS = [
    {'admin_id': 'ADMIN-62B3C81F', 'username': 'adnan', 'email': 'adnangitonga@gmail.com'},
    {'admin_id': 'ADMIN-AB93D02E', 'username': 'charity', 'email': 'charity.k.mutembei@gmail.com'},
]
    
def generate_data(db: Session):
    logger.info("=== Starting database seeding process ===")

    # === 1. Insert Admins ===
    for admin in ADMINS:
        existing_admin = db.query(Admin).filter_by(email=admin["email"]).first()
        if existing_admin:
            logger.info(f"Admin already exists: {admin['email']}")
        else:
            new_admin = Admin(
                admin_id=admin["admin_id"],
                username=admin["username"],
                email=admin["email"]
            )
            db.add(new_admin)
            logger.info(f"Added new admin: {admin['username']}")

    # === 2. Insert Hospitals ===
    for hospital in HOSPITALS:
        existing_hospital = db.query(Hospital).filter_by(email=hospital["email"]).first()
        if existing_hospital:
            logger.info(f"Hospital already exists: {hospital['name']}")
        else:
            new_hospital = Hospital(
                hospital_id=hospital["hospital_id"],
                name=hospital["name"],
                email=hospital["email"],
                phone_number=hospital["phone_number"],
                location=hospital["location"]
            )
            db.add(new_hospital)
            logger.info(f"Added new hospital: {hospital['name']}")

    # === 3. Insert Users ===
    for user in USERS:
        existing_user = db.query(User).filter_by(email=user["email"]).first()
        if existing_user:
            logger.info(f"User already exists: {user['email']}")
        else:
            hospital = db.query(Hospital).filter_by(hospital_id=user["hospital_id"]).first()
            if not hospital:
                logger.warning(f"Skipping user {user['email']} — hospital not found.")
                continue
            new_user = User(
                work_id=user["work_id"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                email=user["email"],
                occupation=user["occupation"],
                department=user["department"],
                hospital_id=hospital.id,
            )
            db.add(new_user)
            logger.info(f"Added new user: {user['first_name']} {user['last_name']}")

    # === Commit changes ===
    db.commit()
    logger.info("=== Database seeding completed successfully ===")