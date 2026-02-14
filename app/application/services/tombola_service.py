from app.application.dtos import (
    StoreAccountDTO, GameAccountDTO, TombolaCharacterDTO, 
    TombolaEventDTO, TombolaDashboardDTO
)
from sqlalchemy.orm import joinedload
from app.application.services.base_service import BaseService
from app.domain.models import (
    Server, StoreAccount, GameAccount, Character, CharacterType,
    TombolaEvent, TombolaActivity, TombolaItemCounter
)
import datetime
from app.utils.logger import logger

class TombolaService(BaseService):

    

    
    def get_tombola_item_counters(self, event_id):
        if not event_id: return {}
        try:
            with self.session_scope() as session:
                counters = session.query(TombolaItemCounter).filter_by(event_id=event_id).all()
                return {counter.item_name: counter.count for counter in counters}
        except Exception as e:
            logger.error(f"Error fetching tombola counters: {e}")
            return {}

    def update_tombola_item_count(self, event_id, item_name, count):
        if not event_id or not item_name: return False
        try:
            with self.session_scope() as session:
                counter = session.query(TombolaItemCounter).filter_by(
                    event_id=event_id, item_name=item_name
                ).first()
                if counter: counter.count = count
                else:
                    new_counter = TombolaItemCounter(
                        event_id=event_id, item_name=item_name, count=count
                    )
                    session.add(new_counter)
                return True
        except Exception as e:
            logger.error(f"Error al actualizar item tombola {item_name}: {e}")
            return False
    
    def get_tombola_events(self, server_id):
        if not server_id: return []
        try:
            with self.session_scope() as session:
                events = session.query(TombolaEvent).filter_by(server_id=server_id).order_by(TombolaEvent.created_at.desc()).all()
                return [TombolaEventDTO(id=e.id, server_id=e.server_id, name=e.name, total_days=30, created_at=e.created_at) for e in events]
        except Exception as e:
            logger.error(f"Error fetching tombola events: {e}")
            return []
    
    def create_tombola_event(self, server_id, event_name):
        if not event_name or not event_name.strip(): return None
        try:
            with self.session_scope() as session:
                event = TombolaEvent(server_id=server_id, name=event_name.strip())
                session.add(event)
                session.flush()
                return TombolaEventDTO(id=event.id, server_id=event.server_id, name=event.name, total_days=30, created_at=event.created_at)
        except Exception as e:
            logger.error(f"Error creating tombola event: {e}")
            return None
    
    def get_tombola_dashboard_data(self, server_id, event_id=None):
        if not server_id or not event_id: return TombolaDashboardDTO()
        try:
            with self.session_scope() as session:
                # 1. Obtener todas las cuentas de juego del servidor
                ga_query = session.query(GameAccount).options(
                    joinedload(GameAccount.store_account),
                    joinedload(GameAccount.characters)
                ).filter(GameAccount.server_id == server_id)
                
                game_accounts = ga_query.all()
                if not game_accounts: return TombolaDashboardDTO()
                
                # 2. Obtener actividades de tómbola
                activity_map = {}
                all_char_ids = [c.id for ga in game_accounts for c in ga.characters]
                if all_char_ids:
                    activities = session.query(TombolaActivity).filter(
                        TombolaActivity.event_id == event_id,
                        TombolaActivity.character_id.in_(all_char_ids)
                    ).all()
                    for act in activities:
                        if act.character_id not in activity_map: activity_map[act.character_id] = {}
                        activity_map[act.character_id][act.day_index] = act.status_code

                # 3. Agrupar por StoreAccount para DTOs
                stores_map = {}
                for ga in game_accounts:
                    store = ga.store_account
                    if store.id not in stores_map:
                        stores_map[store.id] = {
                            'dto': StoreAccountDTO(id=store.id, email=store.email, game_accounts=[]),
                        }
                    
                    char_dtos = [
                        TombolaCharacterDTO(
                            id=c.id, name=c.name,
                            daily_status_map=activity_map.get(c.id, {})
                        ) for c in ga.characters
                    ]
                    
                    ga_dto = GameAccountDTO(id=ga.id, username=ga.username, server_id=ga.server_id, characters=char_dtos)
                    stores_map[store.id]['dto'].game_accounts.append(ga_dto)
                
                return TombolaDashboardDTO(store_accounts=[s['dto'] for s in stores_map.values()])
        except Exception as e:
            logger.error(f"Error en get_tombola_dashboard_data: {e}")
            return TombolaDashboardDTO()
    
    def update_daily_status(self, character_id, day, status, event_id):
        if not event_id: return False
        try:
            with self.session_scope() as session:
                activity = session.query(TombolaActivity).filter_by(
                    character_id=character_id, event_id=event_id, day_index=day
                ).first()
                if activity: activity.status_code = status
                else:
                    new_act = TombolaActivity(
                        character_id=character_id, event_id=event_id, day_index=day, status_code=status
                    )
                    session.add(new_act)
                return True
        except Exception as e:
            logger.error(f"Error updating tombola status: {e}")
            return False

    def get_next_pending_day(self, char_id, event_id):
        if not event_id: return 1
        try:
            with self.session_scope() as session:
                activities = session.query(TombolaActivity).filter_by(
                    character_id=char_id, event_id=event_id
                ).all()
                status_map = {a.day_index: a.status_code for a in activities}
                for d in range(1, 101):
                    if status_map.get(d, 0) == 0: return d
                return 1
        except Exception: return 1

    def get_last_filled_day(self, char_id, event_id):
        if not event_id: return None
        try:
            with self.session_scope() as session:
                last_act = session.query(TombolaActivity).filter(
                    TombolaActivity.character_id == char_id,
                    TombolaActivity.event_id == event_id,
                    TombolaActivity.status_code != 0
                ).order_by(TombolaActivity.day_index.desc()).first()
                return last_act.day_index if last_act else None
        except Exception as e:
            logger.error(f"Error getting last filled day: {e}")
            return None
