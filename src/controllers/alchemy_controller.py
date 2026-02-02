from sqlalchemy.orm import joinedload, sessionmaker
from sqlalchemy import create_engine
from src.utils.config import Config
# IMPORTANTE: Importamos todos los modelos necesarios para las relaciones
from src.models.models import StoreAccount, GameAccount, Character, DailyCorActivity
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
                    grouped_data[store.id] = {'store': store, 'rows': []}
                
                # Ordenar personajes
                sorted_chars = sorted(game_acc.characters, key=lambda x: x.name)
                
                for char in sorted_chars:
                    activity_map = {}
                    for log in char.daily_cors:
                        activity_map[log.date.day] = log.status_code
                    
                    grouped_data[store.id]['rows'].append({
                        'account': game_acc,
                        'character': char,
                        'activity': activity_map
                    })

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
