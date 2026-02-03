from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, Enum, DateTime
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
    name = Column(String(50), unique=True, nullable=False) # Safiro, Rubi, etc.
    
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
    email = Column(String(100), unique=True, nullable=False) # Correo de Tienda
    game_accounts = relationship("GameAccount", back_populates="store_account")

class GameAccount(Base):
    __tablename__ = 'game_accounts'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False) # Ej: Arequito321
    store_account_id = Column(Integer, ForeignKey('store_accounts.id'))
    server_id = Column(Integer, ForeignKey('servers.id')) # Nuevo campo
    
    store_account = relationship("StoreAccount", back_populates="game_accounts")
    server = relationship("Server", back_populates="game_accounts")
    characters = relationship("Character", back_populates="game_account")

class Character(Base):
    __tablename__ = 'characters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False) # Ej: Fachimateria
    char_type = Column(Enum(CharacterType), default=CharacterType.ALCHEMIST)
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
    week = Column(Integer, nullable=False) # 1-5
    status_code = Column(Integer, default=0) # 0=Pending, 1=Done, -1=Failed
    
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

class DailyCorActivity(Base):
    __tablename__ = 'daily_cor_activities'
    
    id = Column(Integer, primary_key=True)
    day_index = Column(Integer, nullable=False)
    status_code = Column(Integer, default=0) # 0=Pendiente, 1=Hecho, -1=Fallido
    
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

class TombolaActivity(Base):
    __tablename__ = 'tombola_activities'
    
    id = Column(Integer, primary_key=True)
    day_index = Column(Integer, nullable=False)  # 1-31
    status_code = Column(Integer, default=0)  # 0=Pendiente, 1=Hecho, -1=Fallido
    
    character_id = Column(Integer, ForeignKey('characters.id'))
    event_id = Column(Integer, ForeignKey('tombola_events.id'))
    
    character = relationship("Character", back_populates="tombola_activities")
    event = relationship("TombolaEvent", back_populates="tombola_activities")

class TimerRecord(Base):
    __tablename__ = 'timer_records'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    elapsed_seconds = Column(Integer, nullable=False)  # Total time in seconds
    created_at = Column(DateTime, default=datetime.datetime.now)
