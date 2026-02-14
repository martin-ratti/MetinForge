import pytest
import sys
import os

# Ensure src is in path
# Ensure src is in path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.domain.base import Base
from app.domain.models import Server, StoreAccount, GameAccount, Character, CharacterType

from sqlalchemy.pool import StaticPool

# Use in-memory SQLite with shared pool for tests
TEST_DATABASE_URL = "sqlite://"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def test_db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def seed_data(test_db):
    """Pre-populates the DB with some basic data for testing."""
    server = Server(name="TestServer", has_dailies=True, has_fishing=True, has_tombola=True)
    test_db.add(server)
    test_db.commit()
    
    store = StoreAccount(email="test@store.com")
    test_db.add(store)
    test_db.commit()
    
    game_acc = GameAccount(username="TestUser", store_account_id=store.id, server_id=server.id)
    test_db.add(game_acc)
    test_db.commit()
    
    char = Character(name="TestChar", char_type=CharacterType.ALCHEMIST, game_account_id=game_acc.id)
    test_db.add(char)
    test_db.commit()
    
    return {
        "server": server,
        "store": store,
        "game_account": game_acc,
        "character": char
    }
