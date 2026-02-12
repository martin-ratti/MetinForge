from sqlalchemy import create_engine
from app.utils.config import Config
from app.domain.base import Base
from app.domain.models import StoreAccount, GameAccount, Character, DailyCorActivity, DailyCorRecord, AlchemyCounter
from app.utils.logger import logger

def init_db():
    engine = create_engine(Config.get_db_url())
    Base.metadata.create_all(engine)
    logger.info("Base de datos inicializada correctamente.")

if __name__ == "__main__":
    init_db()
