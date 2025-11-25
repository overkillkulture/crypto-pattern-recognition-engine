"""Database session management and connection handling."""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

from src.db.models import Base

logger = logging.getLogger(__name__)


class DatabaseSession:
    """
    Database session manager for SQLAlchemy.

    Supports both sync and async operations.
    """

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        use_async: bool = False,
    ):
        """
        Initialize database session manager.

        Args:
            database_url: Database connection URL
            echo: Whether to log SQL statements
            pool_size: Size of connection pool
            max_overflow: Max connections beyond pool_size
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Recycle connections after this many seconds
            use_async: Use async engine (requires asyncpg for PostgreSQL)
        """
        self.database_url = database_url
        self.echo = echo
        self.use_async = use_async

        if use_async:
            # Convert to async URL if needed
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace(
                    "postgresql://", "postgresql+asyncpg://"
                )
            elif database_url.startswith("sqlite://"):
                database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

            self.engine = create_async_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
            )
            self.SessionLocal = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        else:
            self.engine = create_engine(
                database_url,
                echo=echo,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
            )
            self.SessionLocal = scoped_session(
                sessionmaker(
                    bind=self.engine,
                    expire_on_commit=False,
                )
            )

            # Enable foreign keys for SQLite
            if database_url.startswith("sqlite"):
                self._enable_sqlite_foreign_keys(self.engine)

    @staticmethod
    def _enable_sqlite_foreign_keys(engine: Engine):
        """Enable foreign key constraints for SQLite."""

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def create_all(self):
        """Create all tables in the database."""
        if self.use_async:
            raise RuntimeError("Use create_all_async() for async engines")

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    async def create_all_async(self):
        """Create all tables in the database (async)."""
        if not self.use_async:
            raise RuntimeError("Use create_all() for sync engines")

        logger.info("Creating database tables...")
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    def drop_all(self):
        """Drop all tables from the database."""
        if self.use_async:
            raise RuntimeError("Use drop_all_async() for async engines")

        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")

    async def drop_all_async(self):
        """Drop all tables from the database (async)."""
        if not self.use_async:
            raise RuntimeError("Use drop_all() for sync engines")

        logger.warning("Dropping all database tables...")
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions (sync).

        Yields:
            Database session

        Example:
            with db.get_session() as session:
                result = session.query(Model).all()
        """
        if self.use_async:
            raise RuntimeError("Use get_session_async() for async engines")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_session_async(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.

        Yields:
            Async database session

        Example:
            async with db.get_session_async() as session:
                result = await session.execute(select(Model))
        """
        if not self.use_async:
            raise RuntimeError("Use get_session() for sync engines")

        session = self.SessionLocal()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    def close(self):
        """Close the database connection."""
        if self.use_async:
            raise RuntimeError("Use close_async() for async engines")

        logger.info("Closing database connection...")
        self.SessionLocal.remove()
        self.engine.dispose()
        logger.info("Database connection closed")

    async def close_async(self):
        """Close the database connection (async)."""
        if not self.use_async:
            raise RuntimeError("Use close() for sync engines")

        logger.info("Closing database connection...")
        await self.engine.dispose()
        logger.info("Database connection closed")

    def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        if self.use_async:
            raise RuntimeError("Use health_check_async() for async engines")

        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def health_check_async(self) -> bool:
        """
        Check if database connection is healthy (async).

        Returns:
            True if connection is healthy, False otherwise
        """
        if not self.use_async:
            raise RuntimeError("Use health_check() for sync engines")

        try:
            async with self.get_session_async() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance
_db_instance: Optional[DatabaseSession] = None


def init_database(
    database_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    use_async: bool = False,
) -> DatabaseSession:
    """
    Initialize global database instance.

    Args:
        database_url: Database connection URL
        echo: Whether to log SQL statements
        pool_size: Size of connection pool
        max_overflow: Max connections beyond pool_size
        use_async: Use async engine

    Returns:
        Initialized database session manager
    """
    global _db_instance

    if _db_instance is not None:
        logger.warning("Database already initialized, closing existing connection")
        if use_async:
            raise RuntimeError("Cannot close async database synchronously")
        _db_instance.close()

    _db_instance = DatabaseSession(
        database_url=database_url,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        use_async=use_async,
    )

    logger.info(f"Database initialized: {database_url}")
    return _db_instance


def get_database() -> DatabaseSession:
    """
    Get global database instance.

    Returns:
        Database session manager

    Raises:
        RuntimeError: If database not initialized
    """
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance


def get_session() -> Generator[Session, None, None]:
    """
    Get database session (sync).

    Yields:
        Database session

    Example:
        with get_session() as session:
            result = session.query(Model).all()
    """
    db = get_database()
    with db.get_session() as session:
        yield session


async def get_session_async() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session (async).

    Yields:
        Async database session

    Example:
        async with get_session_async() as session:
            result = await session.execute(select(Model))
    """
    db = get_database()
    async with db.get_session_async() as session:
        yield session
