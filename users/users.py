from fastapi import APIRouter, HTTPException, status
from functions import db_dependency, generate_jwt_token, otp_generator
from models import Hospital, User
from redis_client import get_redis_client
from schemas.users_schema import OTPResendSchema, OTPSchema, UserLoginSchema, UserSchema, UserSchemaWithTokens
from logger import logger
from services.send_email import send_otp_email

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

redis_client = get_redis_client()

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

    # Convert ORM user to Pydantic model
    user_model = UserSchema.model_validate(user)

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

@router.get("/")
async def get_all_users(db: db_dependency):
    users = db.query(User).all()
    return users