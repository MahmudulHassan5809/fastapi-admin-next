from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Enum, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from fastapi import FastAPI, Depends
from fastapi_admin_next.controllers import router as admin_router
from fastapi_admin_next.registry import registry
from fastapi_admin_next.db_connect import DBConnector
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from fastapi_admin_next.main import fastapi_admin_next_app
from sqlalchemy.orm import DeclarativeBase
from starlette.middleware.sessions import SessionMiddleware


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


def get_enum_values(enum_class):
    return [member.value for member in enum_class]


class ProfileType(str, PyEnum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    profile_type = Column(
        Enum(ProfileType, values_callable=get_enum_values), nullable=True
    )
    # Products relationship for convenience
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


app = FastAPI()

# User registers their database URL
admin_app = fastapi_admin_next_app.create_app(
    db_url="sqlite+aiosqlite:///./user_database.db"
)


class UserValidation(BaseModel):
    name: str
    email: EmailStr
    profile_type: ProfileType


# Register models with the admin package
registry.register(
    User, filter_fields=["profile_type"], pydantic_validate_class=UserValidation
)
registry.register(Product, filter_fields=["user_id"], search_fields=["title"])

# Include admin routes (no need for user to pass Depends manually)
app.include_router(admin_router)


engine = create_async_engine("sqlite+aiosqlite:///./user_database.db", echo=True)


async def create_db_schema():
    """Create the database schema asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def startup_event():
    """Initialize the database schema on app startup."""
    await create_db_schema()


@app.get("/")
async def read_data(db: AsyncSession = Depends(DBConnector.get_db)):
    # Correct way to access the session inside the context manager
    async with db as session:  # Use the session directly here
        result = await session.execute(
            text("SELECT * FROM users")
        )  # Execute query on the session
        users = result.fetchall()  # Get all users from the result
    return users


app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
