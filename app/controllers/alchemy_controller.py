from sqlalchemy.orm import joinedload
from sqlalchemy import extract
from app.controllers.base_controller import BaseController
# IMPORTANTE: Importamos todos los modelos necesarios para las relaciones
from app.models.models import StoreAccount, GameAccount, Character, DailyCorActivity, CharacterType
from collections import defaultdict
import datetime

class AlchemyController(BaseController):
    # __init__ and get_session inherited from BaseController

    # Nuevo método para obtener servidores
    def get_servers(self):
        Session = self.Session()
        from app.models.models import Server
        try:
            return Session.query(Server).all()
        finally:
            Session.close()

    def create_server(self, name, flags=None):
        session = self.Session()
        from app.models.models import Server
        try:
            if flags is None:
                flags = {'dailies': True, 'fishing': True, 'tombola': True}

            # Original check for existing name is removed as per user's provided snippet.
            # If `name` is empty, the `Server` model might raise an error or it might be handled by the database schema.
            # Assuming `name` is validated elsewhere or is not expected to be empty.
            
            new_server = Server(
                name=name,
                has_dailies=flags.get('dailies', True),
                has_fishing=flags.get('fishing', True),
                has_tombola=flags.get('tombola', True)
            )
            session.add(new_server)
            session.commit()
            return True
        except Exception as e:
            print(f"❌ Error al crear servidor: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_server_flags(self, server_id):
        session = self.Session()
        from app.models.models import Server
        try:
            server = session.query(Server).get(server_id)
            if server:
                return {
                    'has_dailies': server.has_dailies,
                    'has_fishing': server.has_fishing,
                    'has_tombola': server.has_tombola
                }
            return {}
        finally:
            session.close()

    def update_server_feature(self, server_id, feature_key, state):
        session = self.Session()
        from app.models.models import Server
        try:
            server = session.query(Server).get(server_id)
            if not server: return False
            
            if feature_key == 'dailies': server.has_dailies = state
            elif feature_key == 'fishing': server.has_fishing = state
            elif feature_key == 'tombola': server.has_tombola = state
            
            session.commit()
            print(f"Updated Server {server.name} feature {feature_key} to {state}")
            return True
        except Exception as e:
            print(f"Error updating server feature: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def create_store_email(self, email):
        session = self.Session()
        from app.models.models import StoreAccount
        try:
            if not email:
                print("❌ Create Email: Empty email")
                return False
            
            email = email.strip()
            existing = session.query(StoreAccount).filter_by(email=email).first()
            if existing:
                print(f"⚠️ Create Email: Email '{email}' already exists.")
                return False 
            
            new_store = StoreAccount(email=email)
            session.add(new_store)
            session.commit()
            print(f"✅ Create Email: Created '{email}'")
            return True
        except Exception as e:
            print(f"❌ Error al crear email: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def create_game_account(self, server_id, username, slots=5, store_email=None, pj_name="PJ"):
        session = self.Session()
        try:
            print(f"Trying to create account: User={username}, Server={server_id}, Email={store_email}")
            if not username or not store_email: 
                print("❌ Create Account: Missing fields")
                return False

            # Verificar si usuario ya existe (Globalmente, ya que el campo es unique=True)
            if session.query(GameAccount).filter_by(username=username).first():
                print(f"⚠️ Create Account: Username '{username}' already exists globally.")
                return False
            
            store = session.query(StoreAccount).filter_by(email=store_email).first()
            if not store:
                print(f"❌ Create Account: Store email '{store_email}' not found")
                return False
            
            new_account = GameAccount(username=username, server_id=server_id, store_account_id=store.id)
            session.add(new_account)
            session.flush()
            
            # Nombre base para personajes
            base_name = pj_name if pj_name else "PJ"

            for i in range(slots):
                # Usamos nombre + sufijo para unicidad interna, pero en la UI mostraremos el base_name
                # Ejemplo: Reynares_1, Reynares_2...
                char_name_unique = f"{base_name}_{i+1}_{username}" 
                # Agregamos username al final para garantizar unicidad global de nombres de PJ si es necesario?
                # En Metin2 los nicks son unicos. Si el user pone "Reynares" en dos cuentas distintas,
                # internamente debemos diferenciarlos.
                
                char = Character(name=char_name_unique, game_account_id=new_account.id, char_type=CharacterType.ALCHEMIST)
                session.add(char)
            
            session.commit()
            return True
        except Exception as e:
            print(f"❌ Error al crear cuenta: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def update_game_account(self, account_id, new_username, new_slots, new_email=None):
        session = self.Session()
        try:
            account = session.query(GameAccount).get(account_id)
            if not account:
                return False
            
            # Update Username
            if new_username and account.username != new_username:
                account.username = new_username
            
            # Update Email (Store)
            if new_email and account.store_account.email != new_email:
                # Check if new store exists
                store = session.query(StoreAccount).filter_by(email=new_email).first()
                if not store:
                    store = StoreAccount(email=new_email)
                    session.add(store)
                    session.flush()
                account.store_account = store # Reassign
            
            # Update Slots (Characters)
            current_chars = sorted(account.characters, key=lambda x: x.id) # Assuming ID order = creation order
            current_count = len(current_chars)
            
            if new_slots > current_count:
                # Add chars
                to_add = new_slots - current_count
                for i in range(to_add):
                    idx = current_count + i + 1
                    char = Character(name=f"PJ {idx}", game_account_id=account.id, char_type=CharacterType.ALCHEMIST)
                    session.add(char)
            elif new_slots < current_count:
                # Remove chars from end (Only if no data? For now forced)
                to_remove = current_count - new_slots
                # Remove the last ones
                chars_to_delete = current_chars[-to_remove:]
                for char in chars_to_delete:
                    # Generic cleanup (cascade should handle daily_cors if set up, otherwise manual)
                    session.query(DailyCorActivity).filter_by(character_id=char.id).delete()
                    session.delete(char)
            
            session.commit()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar cuenta: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    # --- EVENTOS ALQUIMIA ---
    def create_alchemy_event(self, server_id, name, days):
        session = self.Session()
        from app.models.models import AlchemyEvent
        try:
            new_event = AlchemyEvent(
                server_id=server_id,
                name=name,
                total_days=days,
                created_at=datetime.date.today()
            )
            session.add(new_event)
            session.commit()
            session.refresh(new_event) # Load data so it persists after session close
            return new_event
        except Exception as e:
            print(f"Error creating event: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_alchemy_events(self, server_id):
        session = self.Session()
        from app.models.models import AlchemyEvent
        try:
            return session.query(AlchemyEvent).filter_by(server_id=server_id).order_by(AlchemyEvent.id.desc()).all()
        finally:
            session.close()

    def get_alchemy_dashboard_data(self, server_id, store_email=None, event_id=None):
        """
        Retorna datos filtrados por EVENTO.
        Si no hay evento seleccionado, retorna vacío.
        """
        if not server_id or not event_id:
            return []
            
        session = self.Session()
        try:
            # Consultamos stores que tengan game_accounts en este server
            query = session.query(StoreAccount).filter(StoreAccount.game_accounts.any(GameAccount.server_id == server_id))
            
            if store_email:
                query = query.filter(StoreAccount.email == store_email)
            
            stores = query.all()
            
            grouped_data = {}
            
            for store in stores:
                game_accounts = [acc for acc in store.game_accounts if acc.server_id == server_id]
                if not game_accounts: continue
                
                if store.id not in grouped_data:
                    grouped_data[store.id] = {'store': store, 'accounts': []}
                
                for game_acc in game_accounts:
                    # OBTENER ACTIVIDAD del EVENTO seleccionado
                    if game_acc.characters:
                        first_char = game_acc.characters[0]
                        # Filter by event_id
                        logs = session.query(DailyCorActivity).filter(
                            DailyCorActivity.character_id == first_char.id,
                            DailyCorActivity.event_id == event_id
                        ).all()
                        
                        # Map day_index -> status
                        game_acc.current_event_activity = {log.day_index: log.status_code for log in logs}
                    else:
                        game_acc.current_event_activity = {}
                        
                    grouped_data[store.id]['accounts'].append(game_acc)

            return list(grouped_data.values())

        except Exception as e:
            print(f"❌ Error en Controller: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            session.close()

    def update_daily_status(self, char_id, day_index, new_status, event_id):
        """
        Actualiza el estado para (char_id, event_id, day_index).
        """
        if not event_id: return

        session = self.get_session()
        try:
            # Buscar si existe
            activity = session.query(DailyCorActivity).filter_by(
                character_id=char_id,
                event_id=event_id,
                day_index=day_index
            ).first()

            if activity:
                activity.status_code = new_status
            else:
                new_activity = DailyCorActivity(
                    character_id=char_id,
                    event_id=event_id,
                    day_index=day_index,
                    status_code=new_status
                )
                session.add(new_activity)
            
            session.commit()
            print(f"Updated Char {char_id} Event {event_id} Day {day_index} -> {new_status}")
            
        except Exception as e:
            print(f"❌ Error al guardar estado: {e}")
            session.rollback()
        finally:
            session.close()

    def bulk_import_accounts(self, server_id, import_data):
        """
        Creates accounts and characters from imported data.
        """
        email = import_data.get("email")
        characters = import_data.get("characters", [])
        
        if not email or not characters:
            return False, "Datos incompletos en el archivo."
            
        session = self.Session()
        try:
            # 1. Ensure StoreAccount exists
            store = session.query(StoreAccount).filter_by(email=email).first()
            if not store:
                store = StoreAccount(email=email)
                session.add(store)
                session.flush()
                
            for char_data in characters:
                pj_name = char_data['name']
                slots = char_data['slots']
                
                # Check if character already exists for this store/server
                # Using a simpler check: username based on pj_name
                username = f"{pj_name}_acc"
                
                existing_acc = session.query(GameAccount).filter_by(username=username).first()
                if not existing_acc:
                    new_acc = GameAccount(
                        username=username,
                        store_account_id=store.id,
                        server_id=server_id
                    )
                    session.add(new_acc)
                    session.flush()
                    
                    new_char = Character(
                        name=pj_name,
                        game_account_id=new_acc.id,
                        char_type=CharacterType.ALCHEMIST
                    )
                    session.add(new_char)
            
            session.commit()
            return True, f"Importación exitosa: {len(characters)} personajes cargados."
        except Exception as e:
            session.rollback()
            return False, str(e)
    def get_next_pending_day(self, char_id, event_id):
        """
        Calculates the first day that is NOT completed (or the next one in sequence).
        Returns integer day index (1-based).
        """
        if not event_id: return 1
        
        session = self.Session()
        try:
            # Get all activities for this char & event
            activities = session.query(DailyCorActivity).filter_by(
                character_id=char_id,
                event_id=event_id
            ).order_by(DailyCorActivity.day_index).all()
            
            # Create map of known statuses
            status_map = {a.day_index: a.status_code for a in activities}
            
            # Find first day where status is 0 (Pending) or missing
            # Assuming max 31 days or infinite? Just checking strictly sequential
            # If day 1 is missing/0 -> return 1.
            # If day 1 is done, day 2 is missing -> return 2.
            
            # Let's check up to 100 days just to be safe or max event days
            # Ideally we check gaps. 
            
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
