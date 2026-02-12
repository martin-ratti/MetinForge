from app.utils.db_setup import init_db
from app.domain.base import Base
from app.utils.config import Config
from app.utils.logger import logger
from sqlalchemy import create_engine
import sys

def reset_db():
    logger.info("Conectando a la base de datos...")
    engine = create_engine(Config.get_db_url())
    
    logger.warning("Eliminando tablas existentes...")
    Base.metadata.drop_all(engine)
    
    logger.info("Creando tablas nuevas...")
    Base.metadata.create_all(engine)
    
    logger.info("Base de datos reseteada correctamente.")

if __name__ == "__main__":
    reset_db()
