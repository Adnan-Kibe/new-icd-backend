from pydantic import BaseModel

class UserBaseSchema(BaseModel):
    work_id: str
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True

class UserSchema(UserBaseSchema):
    occupation: str
    department: str
    hospital_id: str

    class Config:
        from_attributes = True

class UserLoginSchema(BaseModel):
    work_id: str
    email: str
    hospital_id: str

    class Config:
        from_attributes = True

class OTPSchema(BaseModel):
    email: str
    otp: str

class OTPResendSchema(BaseModel):
    email: str

class UserSchemaWithTokens(BaseModel):
    access_token: str
    refresh_token: str
    user_details: UserSchema