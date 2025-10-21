from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from typing import List
import uuid

class Base(DeclarativeBase):
    pass

def create_hostpital_id() -> str:
    prefix = "HOSP"
    uuid_str = str(uuid.uuid4()).replace("-", "")[:8].upper()
    return f"{prefix}-{uuid_str}"

def create_admin_id() -> str:
    prefix = "ADMIN"
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
        return f"User(id={self.work_id}, name={self.first_name} {self.last_name}, email={self.email}, occupation={self.occupation}, department={self.department})"

class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hospital_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False, default=create_hostpital_id)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    location: Mapped[str] = mapped_column(String, nullable=False, index=True)

    staff: Mapped[List[User]] = relationship("User", back_populates="hospital", cascade="all, delete-orphan")

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
