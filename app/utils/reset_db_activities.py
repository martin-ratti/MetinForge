from app.utils.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def reset_activities():
    url = Config.get_db_url()
    engine = create_engine(url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("Resetting Daily Activities...")
        # Delete all records from activity tables
        # Adjust table names if necessary (checking models)
        session.execute(text("DELETE FROM daily_cor_activities"))
        session.execute(text("DELETE FROM tombola_activities"))
        session.commit()
        print("✅ Daily activities reset successfully.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error resetting DB: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    reset_activities()
