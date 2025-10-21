from pydantic import BaseModel

class HospitalBase(BaseModel):
    hospital_id: str
    name: str
    email: str
    phone_number: str
    location: str