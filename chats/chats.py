from fastapi import APIRouter

router = APIRouter(
    prefix="/chats",
    tags=['Chats']
)