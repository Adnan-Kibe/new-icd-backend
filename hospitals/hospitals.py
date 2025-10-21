from typing import List
from fastapi import APIRouter
from functions import db_dependency
from models import Hospital
from schemas.hospitals_schema import HospitalBase

router = APIRouter(
    prefix="/hospital",
    tags=['Hospitals']
)

@router.get("/", response_model=List[HospitalBase])
async def get_hospital(db: db_dependency):
    hospitals = db.query(Hospital).all()
    return hospitals