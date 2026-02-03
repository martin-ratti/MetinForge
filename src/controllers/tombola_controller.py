from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.utils.config import Config
from src.models.models import Server, StoreAccount, GameAccount, Character, TombolaEvent, TombolaActivity

class TombolaController:
    def __init__(self):
        engine = create_engine(Config.get_db_url())
        self.Session = sessionmaker(bind=engine)
    
    def get_session(self):
        return self.Session()
    
    def get_servers(self):
        session = self.get_session()
        try:
            return session.query(Server).all()
        finally:
            session.close()
    
    def get_tombola_events(self, server_id):
        """Get all tombola events for a server"""
        session = self.get_session()
        try:
            events = session.query(TombolaEvent).filter(
                TombolaEvent.server_id == server_id
            ).order_by(TombolaEvent.created_at.desc()).all()
            return events
        finally:
            session.close()
    
    def create_tombola_event(self, server_id, event_name):
        """Create a new tombola event (jornada)"""
        session = self.get_session()
        try:
            event = TombolaEvent(
                server_id=server_id,
                name=event_name
            )
            session.add(event)
            session.commit()
            event_id = event.id
            session.refresh(event)
            return event
        except Exception as e:
            session.rollback()
            print(f"Error creating tombola event: {e}")
            return None
        finally:
            session.close()
    
    def get_tombola_dashboard_data(self, server_id, event_id=None):
        """
        Get data for tombola dashboard, filtered by event.
        Returns empty if no event selected.
        """
        if not server_id or not event_id:
            return []
            
        session = self.Session()
        try:
            # Query stores that have game_accounts on this server
            query = session.query(StoreAccount).filter(
                StoreAccount.game_accounts.any(GameAccount.server_id == server_id)
            )
            
            stores_data = query.all()
            
            result = []
            for store in stores_data:
                store_entry = {
                    'store': store,
                    'accounts': []
                }
                
                # Get game accounts for this store on this server
                accounts = session.query(GameAccount).filter(
                    GameAccount.store_account_id == store.id,
                    GameAccount.server_id == server_id
                ).all()
                
                valid_accounts = []
                for ga in accounts:
                    # Get characters
                    chars = session.query(Character).filter(
                        Character.game_account_id == ga.id
                    ).all()
                    
                    if not chars:
                        continue
                    
                    # Get tombola activities for first character in this event
                    first_char = chars[0]
                    activities = session.query(TombolaActivity).filter(
                        TombolaActivity.character_id == first_char.id,
                        TombolaActivity.event_id == event_id
                    ).all()
                    
                    # Build activity map
                    activity_map = {}
                    for act in activities:
                        activity_map[act.day_index] = act.status_code
                    
                    # Attach to game_account
                    ga.current_event_activity = activity_map
                    ga.characters = chars
                    valid_accounts.append(ga)
                
                if valid_accounts:
                    store_entry['accounts'] = valid_accounts
                    result.append(store_entry)
            
            return result
        finally:
            session.close()
    
    def update_daily_status(self, character_id, day, status, event_id):
        """Update or create a tombola activity status for a specific day"""
        session = self.get_session()
        try:
            # Try to find existing activity
            activity = session.query(TombolaActivity).filter(
                TombolaActivity.character_id == character_id,
                TombolaActivity.day_index == day,
                TombolaActivity.event_id == event_id
            ).first()
            
            if activity:
                activity.status_code = status
            else:
                # Create new
                activity = TombolaActivity(
                    character_id=character_id,
                    day_index=day,
                    status_code=status,
                    event_id=event_id
                )
                session.add(activity)
            
            session.commit()
            print(f"Updated character {character_id} day {day} to status {status} for event {event_id}")
        except Exception as e:
            session.rollback()
            print(f"Error updating tombola status: {e}")
        finally:
            session.close()
