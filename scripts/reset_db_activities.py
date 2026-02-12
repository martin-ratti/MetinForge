from app.utils.config import Config
from app.utils.logger import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def reset_activities():
    url = Config.get_db_url()
    engine = create_engine(url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        logger.info("Resetting Daily Activities...")
        # Delete all records from activity tables
        # Adjust table names if necessary (checking models)
        session.execute(text("DELETE FROM daily_cor_activities"))
        session.execute(text("DELETE FROM tombola_activities"))
        session.commit()
        logger.info("Daily activities reset successfully.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error resetting DB: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    reset_activities()
