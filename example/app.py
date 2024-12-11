# pylint: skip-file
# type: ignore

from collections.abc import AsyncGenerator
from enum import Enum as PyEnum

from fastapi import Depends, FastAPI
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from fastapi_admin_next.controllers import router as admin_router
from fastapi_admin_next.db_connect import DBConnector
from fastapi_admin_next.registry import registry


# Utility function for Enum values
def get_enum_values(enum_class):
    return [member.value for member in enum_class]


# Enums
class ProfileType(str, PyEnum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"


# SQLAlchemy Base
class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    profile_type = Column(
        Enum(ProfileType, values_callable=get_enum_values), nullable=True
    )
    products = relationship("Product", back_populates="user")

    def __str__(self):
        return f"{self.name} ({self.email})"


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="products")


# Pydantic Models
class UserValidation(BaseModel):
    name: str
    email: EmailStr
    profile_type: ProfileType


# FastAPI App with Lifespan
DATABASE_URL = "sqlite+aiosqlite:///./user_database.db"
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan context manager for setting up and tearing down resources."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield  # Wait for the application to finish running
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


# Admin App Setup
registry.register(
    User, filter_fields=["profile_type"], pydantic_validate_class=UserValidation
)
registry.register(Product, filter_fields=["user_id"], search_fields=["title"])

# Include Admin Router
app.include_router(admin_router)


# API Endpoints
@app.get("/", response_class=JSONResponse)
async def read_data(db: AsyncSession = Depends(DBConnector.get_db)):
    """Read data from the database."""
    async with db as session:
        result = await session.execute(text("SELECT * FROM users"))
        users = result.fetchall()
    return {"users": users}


# Middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
