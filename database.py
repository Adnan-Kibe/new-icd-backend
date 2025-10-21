import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models import Base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
engine = create_engine(DATABASE_URL)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    with Session(engine) as session:
        yield session