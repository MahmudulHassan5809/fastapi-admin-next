# pylint: skip-file
# type: ignore

from collections.abc import AsyncGenerator
from enum import Enum as PyEnum

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from fastapi_admin_next.main import fastapi_admin_next_app
from fastapi_admin_next.registry import registry


def get_enum_values(enum_class):
    return [member.value for member in enum_class]


class ProfileType(str, PyEnum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


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


class UserValidation(BaseModel):
    name: str
    email: EmailStr
    profile_type: ProfileType


DATABASE_URL = "sqlite+aiosqlite:///./user_database.db"
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan context manager for setting up and tearing down resources."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


# Admin App Setup
admin_app = fastapi_admin_next_app.create_app(db_url=DATABASE_URL)
registry.register(
    User,
    filter_fields=["profile_type"],
    search_fields=["name"],
    pydantic_validate_class=UserValidation,
)
registry.register(Product, filter_fields=["user_id"], search_fields=["title"])

app.mount("/admin", admin_app)
