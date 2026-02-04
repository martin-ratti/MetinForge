from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import Config
from app.models.models import Base, StoreAccount, GameAccount, Character, DailyCorActivity, CharacterType, Server, AlchemyEvent
import datetime
import random

def seed():
    engine = create_engine(Config.get_db_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    print("🌱 Iniciando Seeding (Reset completo)...")
    
    # Reiniciar Base de Datos (Drop & Create)
    try:
        # MySQL fix for foreign keys causing drop_all to fail
        if 'mysql' in Config.get_db_url():
            with engine.connect() as con:
                con.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0;")
                con.commit() # Important for some drivers
        
        Base.metadata.drop_all(engine)
        
        if 'mysql' in Config.get_db_url():
            with engine.connect() as con:
                con.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1;")
                con.commit()

        Base.metadata.create_all(engine)
        print("✅ Esquema recreado (Tablas actualizadas: AlchemyEvent, DailyCorActivity, etc.)")
    except Exception as e:
        print(f"⚠️ Error al recrear esquema: {e}")


    # Base de servidores
    servers = []
    
    # Safiro: Todo activado
    s1 = Server(name="Safiro", has_dailies=True, has_fishing=True, has_tombola=True)
    session.add(s1)
    servers.append(s1)

    # Rubi: Solo pesca y tombola (ejemplo)
    s2 = Server(name="Rubi", has_dailies=True, has_fishing=True, has_tombola=False) 
    session.add(s2)
    servers.append(s2)

    session.commit()

    # Create Default Alchemy Event for each server
    alchemy_events = {}
    for server in servers:
        today = datetime.date.today()
        # Evento de Enero (o mes actual)
        event_name = f"Evento Alquimia {today.strftime('%B %Y')}"
        event = AlchemyEvent(server_id=server.id, name=event_name, total_days=30, created_at=today)
        session.add(event)
        alchemy_events[server.id] = event
    
    session.commit()

    # Crear Tiendas
    stores = []
    for i in range(1, 4):
        store = StoreAccount(email=f"fragmetin{i}@gmail.com")
        session.add(store)
        stores.append(store)
    
    session.commit()

    # Crear Cuentas de Juego y Personajes
    for store in stores:
        for j in range(1, 5): # 4 Cuentas por tienda
            # Asignar servidor aleatorio
            assigned_server = random.choice(servers)
            
            game_acc = GameAccount(
                username=f"Fragmetin{store.id}{j}_{assigned_server.name[0]}", 
                store_account=store,
                server=assigned_server
            )
            session.add(game_acc)
            session.flush() # Need ID
            
            # Crear 5 Personajes por cuenta
            for k in range(5):
                char_name = f"PJ {k+1}"
                char = Character(
                    name=char_name,
                    char_type=CharacterType.ALCHEMIST,
                    game_account_id=game_acc.id # Use explicit ID
                )
                session.add(char)
                session.flush() # Need ID for activities

                # Crear actividad random para el evento actual
                event = alchemy_events[assigned_server.id]
                
                # Simular progreso hasta el da de hoy (ej. dia 15)
                days_progress = 15 
                for day_idx in range(1, days_progress + 1):
                    # 70% chance de tener actividad
                    if random.random() > 0.3:
                        status = 1 if random.random() > 0.2 else -1 # 80% exito, 20% fallo
                        activity = DailyCorActivity(
                            day_index=day_idx,
                            status_code=status,
                            character_id=char.id,
                            event_id=event.id
                        )
                        session.add(activity)

    try:
        session.commit()
        print("✅ Datos de prueba insertados exitosamente.")
    except Exception as e:
        print(f"❌ Error al insertar datos: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed()
