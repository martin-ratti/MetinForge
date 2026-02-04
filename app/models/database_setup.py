from sqlalchemy import create_engine
from app.utils.config import Config
from app.models.base import Base
from app.models.models import StoreAccount, GameAccount, Character, DailyCorActivity, DailyCorRecord, AlchemyCounter

def init_db():
    engine = create_engine(Config.get_db_url())
    # Crea las tablas si no existen
    Base.metadata.create_all(engine)
    print("? Base de datos inicializada correctamente.")

if __name__ == "__main__":
    init_db()
