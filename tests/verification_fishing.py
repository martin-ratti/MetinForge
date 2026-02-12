import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.application.services.fishing_service import FishingService
from app.domain.models import Base, GameAccount, Character, FishingActivity, CharacterType, StoreAccount
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock DB
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Inject Session
class TestFishingService(FishingService):
    def get_session(self):
        return Session()
        
service = TestFishingService()

def test_burst_mode_logic():
    print("Testing Burst Mode Logic...")
    session = Session()
    
    # Setup Data
    store = StoreAccount(email="test@test.com")
    session.add(store)
    session.commit()
    
    acc = GameAccount(username="acc1", store_account_id=store.id, server_id=1)
    session.add(acc)
    session.commit()
    
    char = Character(name="Char1", game_account_id=acc.id, char_type=CharacterType.FISHERMAN)
    session.add(char)
    session.commit()
    
    # Initially Empty
    m, w = service.get_last_filled_week(char.id, 2026)
    print(f"Last Filled (Empty): {m}, {w} -> Expect None, None")
    assert m is None
    
    # Fill Week 1
    service.update_fishing_status(char.id, 2026, 1, 1, 1)
    m, w = service.get_last_filled_week(char.id, 2026)
    print(f"Last Filled (1,1): {m}, {w} -> Expect 1, 1")
    assert m == 1 and w == 1
    
    # Fill Week 2
    service.update_fishing_status(char.id, 2026, 1, 2, -1)
    m, w = service.get_last_filled_week(char.id, 2026)
    print(f"Last Filled (1,2): {m}, {w} -> Expect 1, 2")
    assert m == 1 and w == 2
    
    # Reset Week 2
    service.update_fishing_status(char.id, 2026, 1, 2, 0)
    m, w = service.get_last_filled_week(char.id, 2026)
    print(f"Last Filled (After Reset 1,2): {m}, {w} -> Expect 1, 1")
    assert m == 1 and w == 1
    
    print("Burst Mode Logic: PASS")

def test_import_logic():
    print("\nTesting Import Logic...")
    # Mock parse_account_file return (List of Dicts)
    data = [
        {"email": "import1@test.com", "characters": [{"name": "ImpChar1", "slots": 5}]},
        {"email": "import2@test.com", "characters": [{"name": "ImpChar2", "slots": 5}]}
    ]
    
    # Test Bulk Import with List
    # FishingService returns count of created characters
    count = service.bulk_import_accounts(1, data)
    print(f"Imported Count: {count} -> Expect 2")
    assert count == 2
    
    session = Session()
    char1 = session.query(Character).filter_by(name="ImpChar1").first()
    char2 = session.query(Character).filter_by(name="ImpChar2").first()
    
    print(f"Character 1: {char1.name if char1 else 'None'}")
    print(f"Character 2: {char2.name if char2 else 'None'}")
    
    assert char1 is not None
    assert char2 is not None
    assert char1.char_type == CharacterType.FISHERMAN
    print("Import Logic (List Support): PASS")

if __name__ == "__main__":
    try:
        test_burst_mode_logic()
        test_import_logic()
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
