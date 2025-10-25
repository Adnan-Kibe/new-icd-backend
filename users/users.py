from typing import List
from fastapi import APIRouter, HTTPException, status, Response
from functions import db_dependency, decode_jwt_token, generate_jwt_token, otp_generator, user_dependency
from models import ChatMessage, ChatRoom, Hospital, Participant, User
from schemas.users_schema import OTPResendSchema, OTPSchema, UserLoginSchema, UserSchema, UserSchemaWithTokens
from services.logger import logger
from services.redis_client import get_redis_client
from services.send_email import send_otp_email
from sqlalchemy.orm import selectinload

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

redis_client = get_redis_client()

@router.get("/", response_model=List[UserSchema])
async def get_all_users(db: db_dependency):
    """
    Fetch all users from the database and return them as a list of UserSchema objects.
    """

    # Query all user records from the database
    users = db.query(User).all()

    updated_users = []

    # Loop through each user and map their data into the Pydantic schema
    for user in users:
        # Since hospital_id in the User model is a foreign key reference (int),
        # we fetch the related Hospital's 'hospital_id' string for clarity in the response.
        updated_user = UserSchema(
            work_id=user.work_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            occupation=user.occupation,
            department=user.department,
            hospital_id=user.hospital.hospital_id  # Retrieve readable hospital_id string
        )
        updated_users.append(updated_user)

    # Return the formatted list of user objects as JSON
    return updated_users

@router.post("/login/")
async def login_user(request: UserLoginSchema, db: db_dependency):
    if not request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data was provided")
    
    user = db.query(User).where(User.work_id == request.work_id, User.email == request.email).first()
    if not user:
        logger.warning(f"Unauthorized access by {request.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    hospital = db.query(Hospital).where(Hospital.hospital_id == request.hospital_id).first()
    if not hospital:
        logger.warning(f"Unauthorized access by {request.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")
    
    # Ensure user belongs to this hospital
    if user.hospital_id != hospital.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not part of this hospital")
    
    # Generate OTP
    new_otp = otp_generator()

    try:
        # Cache OTP in Redis for 10 minutes
        key = f"user:{request.email}"
        redis_client.set(key, new_otp, ex=60 * 10)

        # Send OTP email
        result = await send_otp_email(recipient=request.email, otp_code=new_otp)
        if result.get("status") != "success":
            raise Exception("Failed to send OTP email")
        
    except Exception as e:
        logger.error(f"Error sending OTP to {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again."
        )
    
    return result

@router.post("/verify-otp/", response_model=UserSchemaWithTokens)
async def verify_otp(request: OTPSchema, db: db_dependency):
    if not request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No info was provided")
    
    key = f"user:{request.email}"
    stored_otp = redis_client.get(key)

    # Check if OTP exists
    if not stored_otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP expired or not found")

    # Compare OTPs
    if stored_otp != request.otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")
    
    # Remove OTP after successful verification (prevent reuse)
    redis_client.delete(key)
    
    # Retrieve user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    hospital = db.query(Hospital).where(Hospital.id == user.hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")
    


    # Convert ORM user to Pydantic model
    user_model = UserSchema(
        work_id= user.work_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        occupation=user.occupation,
        department=user.department,
        hospital_id=hospital.hospital_id
    )

    # Generate JWT tokens
    access_token = generate_jwt_token(user_model, token_type="access")
    refresh_token = generate_jwt_token(user_model, token_type="refresh")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_details": user_model,
    }

@router.post("/resend-otp/")
async def resend_otp_to_user(request: OTPResendSchema):
    if not request:
        logger.warning("No email was provided for resend OTP")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No email was provided")
    
    key = f"user:{request.email}"

    # Delete old OTP if exists
    if redis_client.exists(key):
        redis_client.delete(key)
        logger.info(f"Old OTP deleted for {request.email}")

    # Generate and store new OTP
    new_otp = otp_generator()
    redis_client.set(key, new_otp, ex=600)

    # Send new OTP
    try:
        result = await send_otp_email(request.email, otp_code=new_otp)
        if result.get("status") != "success":
            raise Exception(result.get("message", "Failed to send OTP email"))
    except Exception as e:
        logger.error(f"Error sending OTP to {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again later."
        )

    return result

from sqlalchemy.orm import selectinload

@router.get("/chats")
async def get_all_personal_chats(db: db_dependency, current_user: user_dependency):
    if not current_user:
        raise HTTPException(status_code=401, detail="User must be logged in")

    user = db.query(User).filter(User.work_id == current_user.work_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    participant_type = user.__class__.__name__

    rooms = (
        db.query(ChatRoom)
        .options(
            selectinload(ChatRoom.participants),
            selectinload(ChatRoom.messages).selectinload(ChatMessage.sender_association)
        )
        .join(ChatRoom.participants)
        .filter(
            Participant.participant_id == user.id,
            Participant.participant_type == participant_type
        )
        .order_by(ChatRoom.last_message.desc())  
        .all()
    )

    chats_data = []
    for room in rooms:
        # Efficiently pick the last message already loaded in memory (since we preloaded messages)
        last_message_obj = (
            max(room.messages, key=lambda m: m.timestamp)
            if room.messages else None
        )

        last_message_data = (
            {
                "id": last_message_obj.id,
                "content": last_message_obj.content,
                "timestamp": last_message_obj.timestamp,
                "sender": {
                    "id": last_message_obj.sender_association.sender_id,
                    "type": last_message_obj.sender_association.sender_type,
                } if last_message_obj.sender_association else None,
            }
            if last_message_obj else None
        )

        chats_data.append({
            "room_id": room.id,
            "room_name": room.name,
            "participants": [
                {"participant_id": p.participant_id, "participant_type": p.participant_type}
                for p in room.participants
            ],
            "last_message": last_message_data,
            "created_at": room.created_at,
        })

    return {"chats": chats_data}