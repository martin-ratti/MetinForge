import sys
import os
from datetime import date
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add project root to path
sys.path.append(os.getcwd())

from app.models.models import Base, Server, StoreAccount, GameAccount, Character, CharacterType, TombolaEvent, AlchemyEvent
from app.utils.config import Config

def seed():
    print("🌱 Seeding database...")
    
    engine = create_engine(Config.get_db_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Create Server
        server = session.query(Server).filter_by(name="Iberia").first()
        if not server:
            server = Server(name="Iberia")
            session.add(server)
            session.commit()
            print("✅ Server 'Iberia' created.")
        else:
            print("ℹ️ Server 'Iberia' already exists.")

        # 2. Create Store Account
        store = session.query(StoreAccount).filter_by(email="test@example.com").first()
        if not store:
            store = StoreAccount(email="test@example.com")
            session.add(store)
            session.commit()
            print("✅ Store 'test@example.com' created.")
        
        # 3. Create Game Account
        game_acc = session.query(GameAccount).filter_by(username="TestUser1").first()
        if not game_acc:
            game_acc = GameAccount(
                username="TestUser1", 
                store_account_id=store.id, 
                server_id=server.id
            )
            session.add(game_acc)
            session.commit()
            print("✅ Game Account 'TestUser1' created.")

        # 4. Create Character
        char = session.query(Character).filter_by(name="TestChar").first()
        if not char:
            char = Character(
                name="TestChar", 
                char_type=CharacterType.ALCHEMIST, 
                game_account_id=game_acc.id
            )
            session.add(char)
            session.commit()
            print("✅ Character 'TestChar' created.")

        # 5. Create Tombola Event
        tombola_event = session.query(TombolaEvent).filter_by(name="Enero 2026").first()
        if not tombola_event:
            tombola_event = TombolaEvent(
                name="Enero 2026",
                server_id=server.id,
                created_at=date.today()
            )
            session.add(tombola_event)
            session.commit()
            print("✅ Tombola Event 'Enero 2026' created.")

        print("✨ Seeding completed successfully!")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed()
