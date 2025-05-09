from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine

Base = declarative_base()

class Database:
    """Handles database connections and sessions."""
    _engine: AsyncEngine = None
    _session_factory = None

    @classmethod
    def initialize(cls, database_url: str, echo: bool = False):
        """Initialize the async engine and sessionmaker."""
        if cls._engine is None:
            cls._engine = create_async_engine(database_url, echo=echo, future=True)
            cls._session_factory = sessionmaker(
                bind=cls._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                future=True
            )

    @classmethod
    def get_session_factory(cls):
        """Return the session factory."""
        if cls._session_factory is None:
            raise ValueError("Database not initialized. Call `initialize()` first.")
        return cls._session_factory

    @classmethod
    async def create_tables(cls):
        """Create all tables defined with Base.metadata."""
        if cls._engine is None:
            raise ValueError("Database not initialized. Call `initialize()` first.")

        # ✅ Important: Dynamically import models so Base knows about them
        from app.models import user_model  # <-- This line ensures models are registered

        async with cls._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
