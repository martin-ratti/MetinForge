from sqlalchemy import create_engine
from src.utils.config import Config
from src.models.base import Base
from src.models.models import StoreAccount, GameAccount, Character, DailyCorActivity

def init_db():
    engine = create_engine(Config.get_db_url())
    # Crea las tablas si no existen
    Base.metadata.create_all(engine)
    print("? Base de datos inicializada correctamente.")

if __name__ == "__main__":
    init_db()
