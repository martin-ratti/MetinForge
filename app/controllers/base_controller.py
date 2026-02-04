from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import Config

class BaseController:
    """
    Base controller that handles database connection and session creation.
    """
    def __init__(self):
        self.engine = create_engine(Config.get_db_url())
        self.Session = sessionmaker(bind=self.engine) # Standard session factory

    def get_session(self):
        """Returns a new session instance."""
        return self.Session()
