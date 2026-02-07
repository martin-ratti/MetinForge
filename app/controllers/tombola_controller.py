from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import create_engine
from app.utils.config import Config
from app.models.models import Server, StoreAccount, GameAccount, Character, TombolaEvent, TombolaActivity

from app.controllers.base_controller import BaseController

class TombolaController(BaseController):
    # __init__ and get_session inherited from BaseController
    
    def get_servers(self):
        session = self.get_session()
        try:
            return session.query(Server).all()
        finally:
            session.close()
    
    def get_tombola_item_counters(self, event_id):
        """Obtiene todos los contadores de items para un evento tombola"""
        if not event_id:
            return {}
            
        session = self.get_session() # Changed from self.Session() to self.get_session() for consistency
        try:
            from app.models.models import TombolaItemCounter
            counters = session.query(TombolaItemCounter).filter_by(event_id=event_id).all()
            return {counter.item_name: counter.count for counter in counters}
        except Exception as e:
            print(f"❌ Error al obtener contadores tombola: {e}")
            return {}
        finally:
            session.close()

    def update_tombola_item_count(self, event_id, item_name, count):
        """Actualiza el contador de un item tombola"""
        if not event_id or not item_name:
            return False
            
        session = self.get_session() # Changed from self.Session() to self.get_session() for consistency
        try:
            from app.models.models import TombolaItemCounter
            counter = session.query(TombolaItemCounter).filter_by(
                event_id=event_id,
                item_name=item_name
            ).first()
            
            if counter:
                counter.count = count
            else:
                new_counter = TombolaItemCounter(
                    event_id=event_id,
                    item_name=item_name,
                    count=count
                )
                session.add(new_counter)
            
            session.commit()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar item tombola: {e}")
            session.rollback()
            return False
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
        if not event_name or not event_name.strip():
            print("❌ Error: Event name cannot be empty.")
            return None

        session = self.get_session()
        try:
            event = TombolaEvent(
                server_id=server_id,
                name=event_name.strip()
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
        Optimized.
        """
        if not server_id or not event_id:
            return []
            
        session = self.Session()
        try:
            # 1. Eager load Store -> Games -> Chars
            query = session.query(StoreAccount).options(
                joinedload(StoreAccount.game_accounts).joinedload(GameAccount.characters)
            ).filter(StoreAccount.game_accounts.any(GameAccount.server_id == server_id))
            
            stores_data = query.all()
            
            # 2. Collect char IDs and fetch activities
            all_char_ids = []
            for store in stores_data:
                for ga in store.game_accounts:
                    if ga.server_id == server_id:
                        for char in ga.characters:
                            all_char_ids.append(char.id)
            
            activity_map = {}
            if all_char_ids:
                activities = session.query(TombolaActivity).filter(
                    TombolaActivity.event_id == event_id,
                    TombolaActivity.character_id.in_(all_char_ids)
                ).all()
                for act in activities:
                    if act.character_id not in activity_map: activity_map[act.character_id] = {}
                    activity_map[act.character_id][act.day_index] = act.status_code

            # 3. Build result
            result = []
            for store in stores_data:
                store_entry = {'store': store, 'accounts': []}
                valid_accounts = []
                for ga in store.game_accounts:
                    if ga.server_id != server_id: continue
                    
                    if not ga.characters: continue

                    first_char = ga.characters[0]
                    ga.current_event_activity = activity_map.get(first_char.id, {})
                    # ga.characters implies it has characters because of the eager load check?
                    # logic in original code: if not chars continue.
                    
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

    def get_next_pending_day(self, char_id, event_id):
        """
        Calculates the first day that is NOT completed.
        Returns integer day index.
        """
        if not event_id: return 1
        
        session = self.Session()
        try:
            activities = session.query(TombolaActivity).filter_by(
                character_id=char_id,
                event_id=event_id
            ).order_by(TombolaActivity.day_index).all()
            
            status_map = {a.day_index: a.status_code for a in activities}
            
            current_day = 1
            while True:
                # If day status is 0 (Pending) or not found -> return it
                if status_map.get(current_day, 0) == 0:
                    return current_day
                current_day += 1
        except Exception as e:
            print(f"Error calculating next pending day: {e}")
            return 1
        finally:
            session.close()
