from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


class DBConnector:
    _engine: AsyncEngine | None = None
    _sessionmaker: async_sessionmaker | None = None  # type: ignore

    @classmethod
    def register_db(cls, database_url: str) -> None:
        """
        Registers the database URL and initializes the engine and sessionmaker.

        Args:
            database_url (str): The database URL to connect to.
        """
        cls._engine = create_async_engine(database_url, echo=True, future=True)
        cls._sessionmaker = async_sessionmaker(bind=cls._engine, expire_on_commit=False)

    @classmethod
    @asynccontextmanager
    async def get_db(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        Provides a database session.

        Yields:
            AsyncSession: An instance of the SQLAlchemy AsyncSession.

        Raises:
            ValueError: If the database is not registered.
        """
        if not cls._sessionmaker:
            raise ValueError(
                "Database is not registered. Call `DBConnector.register_db` first."
            )
        async with cls._sessionmaker() as session:  # pylint: disable=not-callable
            yield session

    @classmethod
    def dependency(cls) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
        """
        Returns a FastAPI dependency for database session.

        Returns:
            Callable[[], AsyncGenerator[AsyncSession, None]]: A callable dependency for FastAPI.
        """

        async def _get_db() -> AsyncGenerator[AsyncSession, None]:
            async with cls.get_db() as session:
                yield session

        return _get_db
