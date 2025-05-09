import os
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from app.database import Database, Base
from app.models import user_model  # Ensure at least one model is loaded

# Match docker-compose service credentials
DB_USER = "user"
DB_PASSWORD = "password"
DB_NAME = "myappdb"
DB_HOST = "postgres" if os.path.exists("/.dockerenv") else "localhost"
DB_PORT = "5432"

TEST_DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def test_initialize_sets_engine_and_session():
    Database._engine = None
    Database._session_factory = None
    Database.initialize(TEST_DB_URL, echo=True)
    assert isinstance(Database._engine, AsyncEngine)
    assert Database._session_factory is not None

def test_get_session_factory_without_init_raises():
    Database._session_factory = None
    with pytest.raises(ValueError, match="Database not initialized."):
        Database.get_session_factory()

def test_get_session_factory_after_init():
    Database._engine = None
    Database._session_factory = None
    Database.initialize(TEST_DB_URL)
    factory = Database.get_session_factory()
    assert callable(factory)

@pytest.mark.asyncio
async def test_create_tables_without_init_raises():
    Database._engine = None
    with pytest.raises(ValueError, match="Database not initialized."):
        await Database.create_tables()

@pytest.mark.asyncio
async def test_create_tables_executes():
    Database._engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
    await Database.create_tables()
    assert "users" in Base.metadata.tables
