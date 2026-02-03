from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.config import Config
from src.models.models import Base, StoreAccount, GameAccount, Character, DailyCorActivity, CharacterType, Server
import datetime
import random

def seed():
    engine = create_engine(Config.get_db_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    print("🌱 Iniciando Seeding (Reset completo)...")
    
    # Reiniciar Base de Datos (Drop & Create)
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
        print("✅ Esquema recreado.")
    except Exception as e:
        print(f"⚠️ Error al recrear esquema: {e}")


    # Base de servidores
    servers = []
    server_names = ["Safiro", "Rubi"]
    for name in server_names:
        srv = Server(name=name)
        session.add(srv)
        servers.append(srv)
    session.commit()

    # Crear Tiendas
    stores = []
    for i in range(1, 4):
        store = StoreAccount(email=f"fragmetin{i}@gmail.com")
        session.add(store)
        stores.append(store)
    
    session.commit()

    # Crear Cuentas de Juego y Personajes
    # Nombres PJ ya no se usan aleatorios, usamos PJ 1..5
    
    for store in stores:
        for j in range(1, 5): # 4 Cuentas por tienda
            # Asignar servidor aleatorio
            assigned_server = random.choice(servers)
            
            game_acc = GameAccount(
                username=f"Fragmetin{store.id}{j}_{assigned_server.name[0]}", # Ej: Fragmetin11_S
                store_account=store,
                server=assigned_server
            )
            session.add(game_acc)
            
            # Crear 5 Personajes por cuenta
            for k in range(5):
                char_name = f"PJ {k+1}"
                char = Character(
                    name=char_name,
                    char_type=CharacterType.ALCHEMIST,
                    game_account=game_acc
                )
                session.add(char)
                
                # Crear actividad random para este mes
                today = datetime.date.today()
                for day in range(1, today.day + 1):
                    # 70% chance de tener actividad
                    if random.random() > 0.3:
                        status = 1 if random.random() > 0.2 else -1 # 80% exito, 20% fallo
                        activity = DailyCorActivity(
                            date=datetime.date(today.year, today.month, day),
                            status_code=status,
                            character=char
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
