from sqlalchemy.orm import joinedload
from sqlalchemy import extract, func
from app.application.services.base_service import BaseService
from app.domain.models import StoreAccount, GameAccount, Character, DailyCorActivity, CharacterType, DailyCorRecord, AlchemyCounter
from collections import defaultdict
import datetime
from app.utils.logger import logger

class AlchemyService(BaseService):

    def get_servers(self):
        """Retorna todos los servidores registrados."""
        session = self.get_session()
        from app.domain.models import Server
        try:
            return session.query(Server).order_by(Server.name).all()
        except Exception as e:
            logger.error(f"Error al obtener servidores: {e}")
            return []
        finally:
            if not self._injected_session:
                session.close()

    def create_server(self, name, flags=None):
        session = self.get_session()
        from app.domain.models import Server
        try:
            if not name or not name.strip():
                logger.error("Error: Server name cannot be empty.")
                return False

            if flags is None:
                flags = {'dailies': True, 'fishing': True, 'tombola': True}
            
            new_server = Server(
                name=name.strip(),
                has_dailies=flags.get('dailies', True),
                has_fishing=flags.get('fishing', True),
                has_tombola=flags.get('tombola', True)
            )
            session.add(new_server)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error al crear servidor: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_server_flags(self, server_id):
        session = self.get_session()
        from app.domain.models import Server
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
        session = self.get_session()
        from app.domain.models import Server
        try:
            server = session.query(Server).get(server_id)
            if not server: return False
            
            if feature_key == 'dailies': server.has_dailies = state
            elif feature_key == 'fishing': server.has_fishing = state
            elif feature_key == 'tombola': server.has_tombola = state
            
            session.commit()
            logger.info(f"Updated Server {server.name} feature {feature_key} to {state}")
            return True
        except Exception as e:
            logger.error(f"Error updating server feature: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def create_store_email(self, email):
        session = self.get_session()
        from app.domain.models import StoreAccount
        try:
            if not email:
                logger.error("Create Email: Empty email")
                return False
            
            email = email.strip()
            existing = session.query(StoreAccount).filter_by(email=email).first()
            if existing:
                logger.warning(f"Create Email: Email '{email}' already exists.")
                return False 
            
            new_store = StoreAccount(email=email)
            session.add(new_store)
            session.commit()
            logger.info(f"Create Email: Created '{email}'")
            return True
        except Exception as e:
            logger.error(f"Error al crear email: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def create_game_account(self, server_id, username, slots=5, store_email=None, pj_name="PJ"):
        session = self.get_session()
        try:
            logger.info(f"Trying to create account: User={username}, Server={server_id}, Email={store_email}")
            if not username or not store_email: 
                logger.error("Create Account: Missing fields")
                return False

            if session.query(GameAccount).filter_by(username=username, server_id=server_id).first():
                logger.warning(f"Create Account: Username '{username}' already exists globally.")
                return False
            
            store = session.query(StoreAccount).filter_by(email=store_email).first()
            if not store:
                logger.error(f"Create Account: Store email '{store_email}' not found")
                return False
            
            new_account = GameAccount(username=username, server_id=server_id, store_account_id=store.id)
            session.add(new_account)
            session.flush()
            
            base_name = pj_name if pj_name else "PJ"

            for i in range(slots):
                char_name_unique = f"{base_name}_{i+1}_{username}" 
                char = Character(name=char_name_unique, game_account_id=new_account.id, char_type=CharacterType.ALCHEMIST)
                session.add(char)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error al crear cuenta: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def update_game_account(self, account_id, new_username, new_slots, new_email=None):
        session = self.get_session()
        try:
            account = session.query(GameAccount).get(account_id)
            if not account:
                return False
            
            if new_username and account.username != new_username:
                account.username = new_username
            
            if new_email and account.store_account.email != new_email:
                store = session.query(StoreAccount).filter_by(email=new_email).first()
                if not store:
                    store = StoreAccount(email=new_email)
                    session.add(store)
                    session.flush()
                account.store_account = store
            
            current_chars = sorted(account.characters, key=lambda x: x.id)
            current_count = len(current_chars)
            
            if new_slots > current_count:
                to_add = new_slots - current_count
                for i in range(to_add):
                    idx = current_count + i + 1
                    char = Character(name=f"PJ {idx}", game_account_id=account.id, char_type=CharacterType.ALCHEMIST)
                    session.add(char)
            elif new_slots < current_count:
                to_remove = current_count - new_slots
                chars_to_delete = current_chars[-to_remove:]
                for char in chars_to_delete:
                    session.query(DailyCorActivity).filter_by(character_id=char.id).delete()
                    session.delete(char)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar cuenta: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    # --- EVENTOS ALQUIMIA ---

    def create_alchemy_event(self, server_id, name, days):
        session = self.get_session()
        from app.domain.models import AlchemyEvent
        try:
            new_event = AlchemyEvent(
                server_id=server_id,
                name=name,
                total_days=days,
                created_at=datetime.date.today()
            )
            session.add(new_event)
            session.commit()
            session.refresh(new_event)
            return new_event
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_alchemy_events(self, server_id):
        session = self.get_session()
        from app.domain.models import AlchemyEvent
        try:
            return session.query(AlchemyEvent).filter_by(server_id=server_id).order_by(AlchemyEvent.id.desc()).all()
        finally:
            session.close()

    def get_alchemy_dashboard_data(self, server_id, store_email=None, event_id=None):
        """Retorna datos de cuentas filtrados por servidor y evento."""
        if not server_id or not event_id:
            return []
            
        session = self.get_session()
        try:
            query = session.query(StoreAccount).options(
                joinedload(StoreAccount.game_accounts).joinedload(GameAccount.characters)
            ).filter(StoreAccount.game_accounts.any(GameAccount.server_id == server_id))
            
            if store_email:
                query = query.filter(StoreAccount.email == store_email)
            
            stores = query.all()
            
            all_char_ids = []
            for store in stores:
                for acc in store.game_accounts:
                    if acc.server_id == server_id:
                        for char in acc.characters:
                            all_char_ids.append(char.id)

            activity_map = {}
            if all_char_ids:
                activities = session.query(DailyCorActivity).filter(
                    DailyCorActivity.event_id == event_id,
                    DailyCorActivity.character_id.in_(all_char_ids)
                ).all()
                for act in activities:
                    if act.character_id not in activity_map: activity_map[act.character_id] = {}
                    activity_map[act.character_id][act.day_index] = act.status_code
            
            grouped_data = []
            for store in stores:
                store_entry = {'store': store, 'accounts': []}
                has_accounts = False
                for game_acc in store.game_accounts:
                    if game_acc.server_id != server_id: continue
                    has_accounts = True
                    
                    if game_acc.characters:
                        first_char = game_acc.characters[0]
                        game_acc.current_event_activity = activity_map.get(first_char.id, {})
                    else:
                        game_acc.current_event_activity = {}
                        
                    store_entry['accounts'].append(game_acc)
                
                if has_accounts: grouped_data.append(store_entry)

            return grouped_data

        except Exception as e:
            logger.exception(f"Error en get_alchemy_dashboard_data: {e}")
            return []
        finally:
            session.close()

    def update_daily_status(self, char_id, day_index, new_status, event_id):
        """Actualiza el estado para (char_id, event_id, day_index)."""
        if not event_id: return

        session = self.get_session()
        try:
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
            logger.info(f"Updated Char {char_id} Event {event_id} Day {day_index} -> {new_status}")
            
        except Exception as e:
            logger.error(f"Error al guardar estado: {e}")
            session.rollback()
        finally:
            session.close()

    def bulk_import_accounts(self, server_id, import_data):
        """Crea cuentas y personajes desde datos importados. Soporta Dict o List[Dict]."""
        if isinstance(import_data, list):
            success_count = 0
            errors = []
            for item in import_data:
                ok, msg = self.bulk_import_accounts(server_id, item)
                if ok: success_count += 1
                else: errors.append(msg)
            
            if success_count > 0:
                return True, f"Importacion masiva: {success_count} grupos procesados. {len(errors)} errores."
            else:
                return False, f"Fallo en importacion. Errores: {'; '.join(errors[:3])}..."

        email = import_data.get("email")
        characters = import_data.get("characters", [])
        
        if not email or not characters:
            return False, "Datos incompletos en el archivo."
            
        count = 0
        session = self.get_session()
        try:
            store = session.query(StoreAccount).filter_by(email=email).first()
            if not store:
                store = StoreAccount(email=email)
                session.add(store)
                session.flush()
                
            for char_data in characters:
                pj_name = char_data['name']
                slots = char_data.get('slots', 5)
                account_name = char_data.get('account_name', pj_name)
                
                existing_acc = session.query(GameAccount).filter_by(username=account_name, server_id=server_id).first()
                if not existing_acc:
                    new_acc = GameAccount(
                        username=account_name,
                        store_account_id=store.id,
                        server_id=server_id
                    )
                    session.add(new_acc)
                    session.flush()
                    
                    new_char = Character(
                        name=pj_name,
                        game_account_id=new_acc.id,
                        char_type=CharacterType.ALCHEMIST,
                        slots=slots
                    )
                    session.add(new_char)
                    count += 1
                else:
                    existing_char = session.query(Character).filter_by(name=pj_name, game_account_id=existing_acc.id).first()
                    if not existing_char:
                        new_char = Character(
                            name=pj_name,
                            game_account_id=existing_acc.id,
                            char_type=CharacterType.ALCHEMIST,
                            slots=slots
                        )
                        session.add(new_char)
                        count += 1
            
            session.commit()
            return True, f"Importacion exitosa: {count} personajes cargados para {email}."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    def get_next_pending_day(self, char_id, event_id):
        """Calcula el primer dia pendiente (no completado) en secuencia."""
        return self._get_next_pending_day_generic(char_id, event_id, DailyCorActivity)

    # --- CORDS ---

    def update_daily_cords(self, game_account_id, event_id, day_index, cords_count):
        """Actualiza o crea el registro de cords para una cuenta en un dia."""
        if not event_id or not game_account_id:
            return False
            
        session = self.get_session()
        try:
            record = session.query(DailyCorRecord).filter_by(
                game_account_id=game_account_id,
                event_id=event_id,
                day_index=day_index
            ).first()
            
            if record:
                record.cords_count = cords_count
            else:
                new_record = DailyCorRecord(
                    game_account_id=game_account_id,
                    event_id=event_id,
                    day_index=day_index,
                    cords_count=cords_count
                )
                session.add(new_record)
            
            session.commit()
            logger.info(f"Cords actualizado: Account {game_account_id}, Day {day_index} -> {cords_count}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar cords: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_daily_cords(self, game_account_id, event_id):
        """Obtiene registros de cords de una cuenta para un evento."""
        if not event_id or not game_account_id:
            return {}
            
        session = self.get_session()
        try:
            records = session.query(DailyCorRecord).filter_by(
                game_account_id=game_account_id,
                event_id=event_id
            ).all()
            
            return {record.day_index: record.cords_count for record in records}
        except Exception as e:
            logger.error(f"Error al obtener cords: {e}")
            return {}
        finally:
            session.close()

    def get_total_cords(self, game_account_id, event_id):
        """Calcula el total de cords acumulados de una cuenta en un evento."""
        if not event_id or not game_account_id:
            return 0
            
        session = self.get_session()
        try:
            result = session.query(func.sum(DailyCorRecord.cords_count)).filter_by(
                game_account_id=game_account_id,
                event_id=event_id
            ).scalar()
            
            return result or 0
        except Exception as e:
            logger.error(f"Error al calcular total cords: {e}")
            return 0
        finally:
            session.close()

    def get_event_cords_summary(self, event_id):
        """Obtiene resumen de cords de todas las cuentas para un evento."""
        if not event_id:
            return {}
            
        session = self.get_session()
        try:
            results = session.query(
                DailyCorRecord.game_account_id,
                func.sum(DailyCorRecord.cords_count).label('total')
            ).filter_by(event_id=event_id).group_by(
                DailyCorRecord.game_account_id
            ).all()
            
            return {acc_id: total for acc_id, total in results}
        except Exception as e:
            logger.error(f"Error al obtener resumen de cords: {e}")
            return {}
        finally:
            session.close()

    def get_all_daily_cords(self, event_id):
        """Obtiene todos los registros diarios de cords para un evento, agrupados por cuenta."""
        if not event_id: return {}
        session = self.get_session()
        try:
            records = session.query(DailyCorRecord).filter_by(event_id=event_id).all()
            result = {}
            for r in records:
                if r.game_account_id not in result:
                    result[r.game_account_id] = {}
                result[r.game_account_id][r.day_index] = r.cords_count
            return result
        except Exception as e:
            logger.error(f"Error al obtener todos los cords: {e}")
            return {}
        finally:
            session.close()

    # --- ALCHEMY COUNTERS ---

    def get_alchemy_counters(self, event_id):
        """Obtiene todos los contadores de alquimia para un evento."""
        if not event_id:
            return {}
            
        session = self.get_session()
        try:
            counters = session.query(AlchemyCounter).filter_by(event_id=event_id).all()
            return {counter.alchemy_type: counter.count for counter in counters}
        except Exception as e:
            logger.error(f"Error al obtener contadores: {e}")
            return {}
        finally:
            session.close()

    def update_alchemy_count(self, event_id, alchemy_type, count):
        """Actualiza el contador de un tipo de alquimia."""
        if not event_id or not alchemy_type:
            return False
            
        session = self.get_session()
        try:
            counter = session.query(AlchemyCounter).filter_by(
                event_id=event_id,
                alchemy_type=alchemy_type
            ).first()
            
            if counter:
                counter.count = count
            else:
                new_counter = AlchemyCounter(
                    event_id=event_id,
                    alchemy_type=alchemy_type,
                    count=count
                )
                session.add(new_counter)
            
            session.commit()
            logger.info(f"Alquimia actualizada: {alchemy_type} -> {count}")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar alquimia: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def increment_alchemy(self, event_id, alchemy_type, amount=1):
        """Incrementa el contador de un tipo de alquimia."""
        if not event_id or not alchemy_type:
            return False
            
        session = self.get_session()
        try:
            counter = session.query(AlchemyCounter).filter_by(
                event_id=event_id,
                alchemy_type=alchemy_type
            ).first()
            
            if counter:
                counter.count += amount
            else:
                new_counter = AlchemyCounter(
                    event_id=event_id,
                    alchemy_type=alchemy_type,
                    count=amount
                )
                session.add(new_counter)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error al incrementar alquimia: {e}")
            session.rollback()
            return False
        finally:
            session.close()
