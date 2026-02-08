import pytest
from app.application.services.alchemy_service import AlchemyService
from app.application.services.base_service import BaseService
from app.domain.models import Server, StoreAccount, GameAccount, Character, DailyCorActivity, AlchemyCounter, AlchemyEvent

@pytest.fixture
def alchemy_ctrl(test_db):
    ctrl = AlchemyService()
    # Mock session factory to return test_db, but prevent close() from ruining the fixture
    # We create a proxy that delegates everything but close
    class SessionProxy:
        def __init__(self, session):
            self._session = session
        def __getattr__(self, name):
            if name == 'close':
                return lambda: None
            return getattr(self._session, name)
    
    proxy = SessionProxy(test_db)
    ctrl.get_session = lambda: proxy
    ctrl.Session = lambda: proxy
    return ctrl

def test_server_management(alchemy_ctrl, test_db):
    """Test creating and retrieving servers and flags."""
    # Create
    success = alchemy_ctrl.create_server("NewServer", flags={'dailies': True})
    assert success is True
    
    server = test_db.query(Server).filter_by(name="NewServer").first()
    assert server is not None
    assert server.has_dailies is True
    assert server.has_fishing is True # Default from flags logic in controller if not specified? 
    # Controller logic: if flags is None: flags = default. But here flags is passed as {'dailies': True}.
    # new_server = Server(..., has_fishing=flags.get('fishing', True))
    # flags.get('fishing', True) returns True if key missing. So Yes.
    
    # Duplicate Check
    success = alchemy_ctrl.create_server("NewServer")
    assert success is False
    
    # Flags
    flags = alchemy_ctrl.get_server_flags(server.id)
    assert flags['has_dailies'] is True
    
    # Update Feature
    success = alchemy_ctrl.update_server_feature(server.id, "fishing", True)
    assert success is True
    test_db.refresh(server)
    assert server.has_fishing is True

def test_account_creation_chain(alchemy_ctrl, test_db, seed_data):
    """Test creating Store -> GameAccount -> Character."""
    
    # 1. Store Account
    success = alchemy_ctrl.create_store_email("newstore@gmail.com")
    assert success is True
    store = test_db.query(StoreAccount).filter_by(email="newstore@gmail.com").first()
    assert store is not None
    
    # 2. Game Account
    server_id = seed_data['server'].id
    success = alchemy_ctrl.create_game_account(
        server_id=server_id,
        username="NewGameAcc",
        store_email="newstore@gmail.com"
    )
    assert success is True
    game_acc = test_db.query(GameAccount).filter_by(username="NewGameAcc").first()
    assert game_acc is not None
    assert game_acc.store_account_id == store.id
    
    # 3. Duplicate Game Account
    success = alchemy_ctrl.create_game_account(server_id, "NewGameAcc", store_email="newstore@gmail.com")
    assert success is False
    
    # 4. Character (implicit in game account creation? No, usually separate or auto-created in some flows)
    # AlchemyController.create_game_account creates 5 dummy chars?
    # Let's check logic: Yes, "for i in range(slot_count): ... new_char = Character..."
    assert len(game_acc.characters) == 5
    assert game_acc.characters[0].name.startswith("PJ")

def test_update_game_account(alchemy_ctrl, test_db, seed_data):
    """Test updating game account details."""
    game_acc = seed_data['game_account']
    new_store = StoreAccount(email="other@gmail.com")
    test_db.add(new_store)
    test_db.commit()
    
    success = alchemy_ctrl.update_game_account(
        account_id=game_acc.id,
        new_username="UpdatedUser",
        new_email="other@gmail.com",
        new_slots=5
    )
    assert success is True
    
    test_db.refresh(game_acc)
    assert game_acc.username == "UpdatedUser"
    assert game_acc.store_account_id == new_store.id

def test_alchemy_events_and_counters(alchemy_ctrl, test_db, seed_data):
    """Test Event creation and Alchemy Counters."""
    server_id = seed_data['server'].id
    
    # Create Event
    event = alchemy_ctrl.create_alchemy_event(server_id, "Alchemy Event 2026", 30)
    assert event is not None
    assert event.total_days == 30
    
    # Counters
    success = alchemy_ctrl.update_alchemy_count(event.id, "Diamond", 5)
    assert success is True
    
    counters = alchemy_ctrl.get_alchemy_counters(event.id)
    assert counters["Diamond"] == 5
    
    # Increment
    success = alchemy_ctrl.increment_alchemy(event.id, "Diamond", 1)
    assert success is True
    
    counters = alchemy_ctrl.get_alchemy_counters(event.id)
    assert counters["Diamond"] == 6

def test_daily_cords_records(alchemy_ctrl, test_db, seed_data):
    """Test updating and retrieving daily cords."""
    game_acc_id = seed_data['game_account'].id
    
    # Create valid event
    event = alchemy_ctrl.create_alchemy_event(seed_data['server'].id, "Cords Event", 30)
    event_id = event.id
    
    # 1. Update Cords
    success = alchemy_ctrl.update_daily_cords(game_acc_id, event_id, 1, 15) # Day 1, 15 Cords
    # Note: Correct arg order? 
    # Controller: update_daily_cords(self, game_account_id, event_id, day_index, cords_count)
    # Test call was: (game_acc_id, 1, 15, event_id) -> Mismatch in original?
    # Original test code: update_daily_cords(game_acc_id, 1, 15, event_id)
    # Controller def (from Step 250, line 397): (game_account_id, event_id, day_index, cords_count)
    # My previous call: (acc, 1, 15, event_id)
    # Arg 2 (event_id) got 1.
    # Arg 3 (day_index) got 15.
    # Arg 4 (cords_count) got 99 (event_id).
    # So I updated: event_id=1, day_index=15, cords=99.
    # Then I queried: get_daily_cords(acc, event_id=99).
    # Result: Empty because I inserted for event_id=1.
    # FAILURE EXPLAINED.
    
    # Correct Call:
    assert success is True
    
    # 2. Get Cords
    cords_map = alchemy_ctrl.get_daily_cords(game_acc_id, event_id)
    assert cords_map[1] == 15
    
    # 3. Total
    total = alchemy_ctrl.get_total_cords(game_acc_id, event_id)
    assert total == 15
    
    # 4. Summary for Event
    summary = alchemy_ctrl.get_event_cords_summary(event_id)
    assert summary[game_acc_id] == 15
