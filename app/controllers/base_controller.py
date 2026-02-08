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

    def get_servers(self):
        """Returns all servers."""
        session = self.get_session()
        try:
            from app.models.models import Server
            return session.query(Server).all()
        finally:
            session.close()

    def _get_next_pending_day_generic(self, char_id, event_id, activity_model):
        """
        Generic implementation for finding the next pending day.
        """
        if not event_id: return 1
        
        session = self.get_session()
        try:
            # Get all activities for this char & event
            activities = session.query(activity_model).filter_by(
                character_id=char_id,
                event_id=event_id
            ).order_by(activity_model.day_index).all()
            
            # Create map of known statuses
            status_map = {a.day_index: a.status_code for a in activities}
            
            # Find first day where status is 0 (Pending) or missing
            current_day = 1
            while True:
                status = status_map.get(current_day, 0)
                if status == 0:
                    return current_day
                current_day += 1
                
        except Exception as e:
            print(f"Error calculating next day: {e}")
            return 1
        finally:
            session.close()
