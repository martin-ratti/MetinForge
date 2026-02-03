from sqlalchemy.orm import joinedload, sessionmaker
from sqlalchemy import create_engine
from src.utils.config import Config
# IMPORTANTE: Importamos todos los modelos necesarios para las relaciones
from src.models.models import StoreAccount, GameAccount, Character, DailyCorActivity, CharacterType
from collections import defaultdict
import datetime

class AlchemyController:
    def __init__(self):
        engine = create_engine(Config.get_db_url())
        self.Session = sessionmaker(bind=engine)

    # Nuevo método para obtener servidores
    def get_servers(self):
        Session = self.Session()
        from src.models.models import Server
        try:
            return Session.query(Server).all()
        finally:
            Session.close()

    def create_server(self, name):
        session = self.Session()
        from src.models.models import Server
        try:
            if not name or session.query(Server).filter_by(name=name).first():
                return False
            
            new_server = Server(name=name)
            session.add(new_server)
            session.commit()
            return True
        except Exception as e:
            print(f"❌ Error al crear servidor: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def create_store_email(self, email):
        session = self.Session()
        from src.models.models import StoreAccount
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

    def get_alchemy_dashboard_data(self, server_id=None):
        """
        Retorna los datos filtrados por servidor.
        Si server_id es None, retorna lista vacía (o todo, según lógica, pero para UI multi-server mejor esperar selección).
        """
        if not server_id:
            return []

        session = self.Session()
        try:
            # Consultamos las cuentas de juego que pertenecen a ese servidor
            # y hacemos join con su tienda y sus personajes+actividad
            game_accounts = session.query(GameAccount).filter_by(server_id=server_id).options(
                joinedload(GameAccount.store_account),
                joinedload(GameAccount.characters).joinedload(Character.daily_cors)
            ).all()

            # Agrupar por Tienda
            # Usamos un diccionario para agrupar: {store_id: {'store': store_obj, 'rows': []}}
            grouped_data = {}

            for game_acc in game_accounts:
                store = game_acc.store_account
                if store.id not in grouped_data:
                    grouped_data[store.id] = {'store': store, 'accounts': []}
                
                # Pre-proceso para la vista:
                # Cada cuenta tendrá su lista de personajes, pero la vista renderizará UNA fila por cuenta.
                # La actividad visualizada dependerá de... ¿el primer personaje? ¿o un resumen?
                # Por ahora pasamos la cuenta entera.
                
                grouped_data[store.id]['accounts'].append(game_acc)

            # Convert to list but keep structure expected by View?
            # View espera [{'store': ..., 'rows': [...]}] -> Cambiemos 'rows' a 'accounts' o adaptamos View.
            # Cambiaremos la estructura de retorno a:
            # list of {'store': store, 'accounts': [game_account_obj, ...]}
            
            return list(grouped_data.values())

        except Exception as e:
            print(f"❌ Error en Controller: {e}")
            return []
        finally:
            session.close()

    def update_daily_status(self, char_id, day, new_status):
        """
        Actualiza o crea el registro de actividad diaria para un personaje.
        Asume el mes y año actual por ahora.
        """
        session = self.Session()
        try:
            # Construir la fecha correcta del mes actual
            now = datetime.datetime.now()
            try:
                # Intentamos crear la fecha (ej: 30 de febrero daría error)
                target_date = datetime.date(now.year, now.month, day)
            except ValueError:
                print(f"⚠️ Fecha inválida: Día {day} no existe en el mes actual.")
                return

            # Buscar si ya existe el registro
            activity = session.query(DailyCorActivity).filter_by(
                character_id=char_id,
                date=target_date
            ).first()

            if activity:
                # Actualizar existente
                activity.status_code = new_status
                print(f"🔄 Actualizando: Char {char_id} - {target_date} -> {new_status}")
            else:
                # Crear nuevo
                new_activity = DailyCorActivity(
                    character_id=char_id,
                    date=target_date,
                    status_code=new_status
                )
                session.add(new_activity)
                print(f"➕ Creando: Char {char_id} - {target_date} -> {new_status}")
            
            session.commit()
            
        except Exception as e:
            print(f"❌ Error al guardar estado: {e}")
            session.rollback()
        finally:
            session.close()
