from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from .base import Base
import enum

class CharacterType(enum.Enum):
    ALCHEMIST = "alchemist"
    FISHERMAN = "fisherman"

class Server(Base):
    __tablename__ = 'servers'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False) # Safiro, Rubi, etc.
    game_accounts = relationship("GameAccount", back_populates="server")

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

class DailyCorActivity(Base):
    __tablename__ = 'daily_cor_activities'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    status_code = Column(Integer, default=0) # 0=Pendiente, 1=Hecho, -1=Fallido (Logica Excel)
    character_id = Column(Integer, ForeignKey('characters.id'))
    
    character = relationship("Character", back_populates="daily_cors")

# Aqu� irian logs de pesca...
