from app.models.database_setup import init_db
from app.models.base import Base
from app.utils.config import Config
from sqlalchemy import create_engine
import sys

def reset_db():
    print("🔄 Conectando a la base de datos...")
    engine = create_engine(Config.get_db_url())
    
    print("⚠ Eliminando tablas existentes...")
    Base.metadata.drop_all(engine)
    
    print("✨ Creando tablas nuevas...")
    Base.metadata.create_all(engine)
    
    print("✅ Base de datos reseteada correctamente.")

if __name__ == "__main__":
    reset_db()
