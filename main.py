from fastapi import FastAPI
from database import init_db
from users import users_router
from contextlib import asynccontextmanager
from functions import generate_data
from sqlalchemy.orm import Session
from database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("Initializing the Database")
        init_db()
        print("Database Initialized")

        with Session(engine) as db:
            generate_data(db)
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise
    
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(users_router)