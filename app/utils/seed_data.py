from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import Config
from app.domain.models import Base, StoreAccount, GameAccount, Character, DailyCorActivity, DailyCorRecord, CharacterType, Server, AlchemyEvent
import datetime
import random

from app.utils.logger import logger

def seed():
    engine = create_engine(Config.get_db_url())
    Session = sessionmaker(bind=engine)

    logger.info("Iniciando Seeding (Reset completo)...")
    
    try:
        if 'mysql' in Config.get_db_url():
            with engine.connect() as con:
                con.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0;")
                con.commit()
        
        Base.metadata.drop_all(engine)
        
        if 'mysql' in Config.get_db_url():
            with engine.connect() as con:
                con.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1;")
                con.commit()

        Base.metadata.create_all(engine)
        logger.info("Esquema recreado.")
    except Exception as e:
        logger.error(f"Error al recrear esquema: {e}")
        return

    # Session created AFTER schema operations to avoid deadlock
    session = Session()

    servers = []
    
    s1 = Server(name="Safiro", has_dailies=True, has_fishing=True, has_tombola=True)
    session.add(s1)
    servers.append(s1)

    s2 = Server(name="Rubi", has_dailies=True, has_fishing=True, has_tombola=False) 
    session.add(s2)
    servers.append(s2)

    session.commit()

    # Eventos de Alquimia
    alchemy_events = {}
    for server in servers:
        today = datetime.date.today()
        event_name = f"Evento Alquimia {today.strftime('%B %Y')}"
        event = AlchemyEvent(server_id=server.id, name=event_name, total_days=30, created_at=today)
        session.add(event)
        alchemy_events[server.id] = event
    
    session.commit()

    # Tiendas
    stores = []
    for i in range(1, 4):
        store = StoreAccount(email=f"fragmetin{i}@gmail.com")
        session.add(store)
        stores.append(store)
    
    session.commit()

    # Cuentas de Juego y Personajes
    for store in stores:
        for j in range(1, 5):
            assigned_server = random.choice(servers)
            
            game_acc = GameAccount(
                username=f"Fragmetin{store.id}{j}_{assigned_server.name[0]}", 
                store_account=store,
                server=assigned_server
            )
            session.add(game_acc)
            session.flush()
            
            for k in range(5):
                char = Character(
                    name=f"PJ {k+1}",
                    char_type=CharacterType.ALCHEMIST,
                    game_account_id=game_acc.id
                )
                session.add(char)
                session.flush()

                event = alchemy_events[assigned_server.id]
                days_progress = 15 
                for day_idx in range(1, days_progress + 1):
                    if random.random() > 0.3:
                        status = 1 if random.random() > 0.2 else -1
                        activity = DailyCorActivity(
                            day_index=day_idx,
                            status_code=status,
                            character_id=char.id,
                            event_id=event.id
                        )
                        session.add(activity)
                        session.add(DailyCorRecord(
                            game_account_id=game_acc.id, 
                            event_id=event.id, 
                            day_index=day_idx, 
                            cords_count=1 if status == 1 else 0
                        ))

    try:
        session.commit()
        logger.info("Datos de prueba insertados exitosamente.")
    except Exception as e:
        logger.error(f"Error al insertar datos: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed()
