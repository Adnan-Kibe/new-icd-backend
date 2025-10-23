from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Integer, String, ForeignKey
from typing import List
import uuid


class Base(DeclarativeBase):
    pass

def create_hospital_id() -> str:
    prefix = "HOSP"
    uuid_str = str(uuid.uuid4()).replace("-", "")[:8].upper()
    return f"{prefix}-{uuid_str}"

def create_admin_id() -> str:
    prefix = "ADMIN"
    uuid_str = str(uuid.uuid4()).replace("-", "")[:8].upper()
    return f"{prefix}-{uuid_str}"

def create_chat_id() -> str:
    prefix = "CHAT"
    uuid_str = str(uuid.uuid4()).replace("-", "")[:8].upper()
    return f"{prefix}-{uuid_str}"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    work_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    occupation: Mapped[str] = mapped_column(String, nullable=False, index=True)
    department: Mapped[str] = mapped_column(String, nullable=False, index=True)

    hospital_id: Mapped[int] = mapped_column(Integer, ForeignKey("hospitals.id"), nullable=False)
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="staff")

    def __repr__(self) -> str:
        return f"User(id={self.work_id}, name={self.first_name} {self.last_name}, email={self.email})"


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hospital_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False, default=create_hospital_id)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    location: Mapped[str] = mapped_column(String, nullable=False, index=True)

    staff: Mapped[List["User"]] = relationship("User", back_populates="hospital", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Hospital(id={self.hospital_id}, name={self.name}, email={self.email})"

    def staff_count(self) -> int:
        return len(self.staff)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admin_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False, default=create_admin_id)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Admin(id={self.admin_id}, username={self.username}, email={self.email})"


class ChatRoom(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True, unique=True, nullable=False, index=True, default=create_chat_id)
    name: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ChatMessage(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, unique=True, default=lambda: str(uuid.uuid4()))
    message: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    room_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id"))
    room: Mapped["ChatRoom"] = relationship(back_populates="messages")

    sender_association: Mapped["MessageSender"] = relationship("MessageSender", back_populates="message", uselist=False)


class MessageSender(Base):
    __tablename__ = "message_senders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String, ForeignKey("messages.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sender_type: Mapped[str] = mapped_column(String, nullable=False)

    message: Mapped["ChatMessage"] = relationship("ChatMessage", back_populates="sender_association")

    def __repr__(self):
        return f"<MessageSender(type={self.sender_type}, sender_id={self.sender_id})>"
