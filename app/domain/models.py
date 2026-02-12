from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import enum

class CharacterType(enum.Enum):
    ALCHEMIST = "alchemist"
    FISHERMAN = "fisherman"

class Server(Base):
    __tablename__ = 'servers'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    
    # Feature Flags
    has_dailies = Column(Boolean, default=True)
    has_fishing = Column(Boolean, default=True)
    has_tombola = Column(Boolean, default=True)

    game_accounts = relationship("GameAccount", back_populates="server")
    alchemy_events = relationship("AlchemyEvent", back_populates="server")
    tombola_events = relationship("TombolaEvent", back_populates="server")

class StoreAccount(Base):
    __tablename__ = 'store_accounts'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    game_accounts = relationship("GameAccount", back_populates="store_account")

class GameAccount(Base):
    __tablename__ = 'game_accounts'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False) # Removed unique=True
    store_account_id = Column(Integer, ForeignKey('store_accounts.id'))
    server_id = Column(Integer, ForeignKey('servers.id'))
    
    __table_args__ = (
        UniqueConstraint('username', 'server_id', name='uq_game_account_username_server'),
    )

    
    store_account = relationship("StoreAccount", back_populates="game_accounts")
    server = relationship("Server", back_populates="game_accounts")
    characters = relationship("Character", back_populates="game_account")
    daily_cor_records = relationship("DailyCorRecord", back_populates="game_account")

class Character(Base):
    __tablename__ = 'characters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    char_type = Column(Enum(CharacterType), default=CharacterType.ALCHEMIST)
    slots = Column(Integer, default=5) # Added to support import data
    game_account_id = Column(Integer, ForeignKey('game_accounts.id'))
    
    game_account = relationship("GameAccount", back_populates="characters")
    daily_cors = relationship("DailyCorActivity", back_populates="character")
    fishing_activities = relationship("FishingActivity", back_populates="character")
    tombola_activities = relationship("TombolaActivity", back_populates="character")

class FishingActivity(Base):
    __tablename__ = 'fishing_activities'
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    status_code = Column(Integer, default=0)
    
    character_id = Column(Integer, ForeignKey('characters.id'))
    character = relationship("Character", back_populates="fishing_activities")

class AlchemyEvent(Base):
    __tablename__ = 'alchemy_events'

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('servers.id'))
    name = Column(String(100), nullable=False)
    total_days = Column(Integer, default=30)
    created_at = Column(Date, default=datetime.date.today)

    server = relationship("Server", back_populates="alchemy_events")
    daily_activities = relationship("DailyCorActivity", back_populates="event")
    daily_cor_records = relationship("DailyCorRecord", back_populates="event")
    alchemy_counters = relationship("AlchemyCounter", back_populates="event")

class DailyCorActivity(Base):
    __tablename__ = 'daily_cor_activities'
    
    id = Column(Integer, primary_key=True)
    day_index = Column(Integer, nullable=False)
    status_code = Column(Integer, default=0)
    
    character_id = Column(Integer, ForeignKey('characters.id'))
    event_id = Column(Integer, ForeignKey('alchemy_events.id'))
    
    character = relationship("Character", back_populates="daily_cors")
    event = relationship("AlchemyEvent", back_populates="daily_activities")

class TombolaEvent(Base):
    __tablename__ = 'tombola_events'

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('servers.id'))
    name = Column(String(100), nullable=False)
    created_at = Column(Date, default=datetime.date.today)

    server = relationship("Server", back_populates="tombola_events")
    tombola_activities = relationship("TombolaActivity", back_populates="event")
    item_counters = relationship("TombolaItemCounter", back_populates="event")

class TombolaActivity(Base):
    __tablename__ = 'tombola_activities'
    
    id = Column(Integer, primary_key=True)
    day_index = Column(Integer, nullable=False)
    status_code = Column(Integer, default=0)
    
    character_id = Column(Integer, ForeignKey('characters.id'))
    event_id = Column(Integer, ForeignKey('tombola_events.id'))
    
    character = relationship("Character", back_populates="tombola_activities")
    event = relationship("TombolaEvent", back_populates="tombola_activities")

class TombolaItemCounter(Base):
    """Contadores de items para tombola por evento"""
    __tablename__ = 'tombola_item_counters'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('tombola_events.id'))
    item_name = Column(String(50), nullable=False)
    count = Column(Integer, default=0)
    
    event = relationship("TombolaEvent", back_populates="item_counters")

class TimerRecord(Base):
    __tablename__ = 'timer_records'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    elapsed_seconds = Column(Integer, nullable=False)  # Total time in seconds
    created_at = Column(DateTime, default=datetime.datetime.now)

class DailyCorRecord(Base):
    """Registro de cords por cuenta por día dentro de un evento"""
    __tablename__ = 'daily_cor_records'
    
    id = Column(Integer, primary_key=True)
    game_account_id = Column(Integer, ForeignKey('game_accounts.id'))
    event_id = Column(Integer, ForeignKey('alchemy_events.id'))
    day_index = Column(Integer, nullable=False)  # Día del evento (1-based)
    cords_count = Column(Integer, default=0)  # Cantidad de cords ese día
    
    game_account = relationship("GameAccount", back_populates="daily_cor_records")
    event = relationship("AlchemyEvent", back_populates="daily_cor_records")

class AlchemyCounter(Base):
    """Contadores de alquimias por evento (globales del servidor)"""
    __tablename__ = 'alchemy_counters'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('alchemy_events.id'))
    alchemy_type = Column(String(20), nullable=False)  # diamante, rubi, jade, zafiro, granate, onice
    count = Column(Integer, default=0)
    
    event = relationship("AlchemyEvent", back_populates="alchemy_counters")

