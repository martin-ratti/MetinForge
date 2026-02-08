import pytest
from app.controllers.tombola_controller import TombolaController
from app.models.models import TombolaActivity, TombolaEvent, TombolaItemCounter

@pytest.fixture
def tombola_ctrl(test_db):
    ctrl = TombolaController()
    class SessionProxy:
        def __init__(self, session): self._session = session
        def __getattr__(self, name):
            if name == 'close': return lambda: None
            return getattr(self._session, name)
    
    proxy = SessionProxy(test_db)
    ctrl.get_session = lambda: proxy
    ctrl.Session = lambda: proxy
    return ctrl

def test_tombola_event_lifecycle(tombola_ctrl, test_db, seed_data):
    """Test creating and retrieving tombola events."""
    controller = tombola_ctrl
    
    server_id = seed_data['server'].id
    
    # Create Event
    event = controller.create_tombola_event(server_id, "Summer 2026")
    assert event is not None
    assert event.name == "Summer 2026"
    assert event.server_id == server_id
    
    # Retrieve Events
    events = controller.get_tombola_events(server_id)
    assert len(events) >= 1
    assert events[0].name == "Summer 2026"
    
    # Fail Create (Empty name)
    fail_event = controller.create_tombola_event(server_id, "")
    assert fail_event is None

def test_tombola_item_counters(tombola_ctrl, test_db, seed_data):
    """Test managing tombola item counters."""
    controller = tombola_ctrl
    
    # Need a tombola event logic, let's use the one from seed or create new
    # Seed data doesn't explicitly create TombolaEvent usually, so let's create one
    event = controller.create_tombola_event(seed_data['server'].id, "Items Event")
    event_id = event.id
    
    # Update Item
    success = controller.update_tombola_item_count(event_id, "Sun Elixir", 10)
    assert success is True
    
    # Verify in DB
    counter = test_db.query(TombolaItemCounter).filter_by(event_id=event_id, item_name="Sun Elixir").first()
    assert counter is not None
    assert counter.count == 10
    
    # Update Existing
    success = controller.update_tombola_item_count(event_id, "Sun Elixir", 25)
    assert success is True
    test_db.refresh(counter)
    assert counter.count == 25
    
    # Get Counters
    counters_map = controller.get_tombola_item_counters(event_id)
    assert "Sun Elixir" in counters_map
    assert counters_map["Sun Elixir"] == 25

def test_tombola_status_updates(tombola_ctrl, test_db, seed_data):
    """Test updating daily status."""
    controller = tombola_ctrl
    
    char_id = seed_data['character'].id
    event = controller.create_tombola_event(seed_data['server'].id, "Status Event")
    event_id = event.id
    
    # Create status
    controller.update_daily_status(char_id, day=1, status=1, event_id=event_id)
    
    act = test_db.query(TombolaActivity).filter_by(
        character_id=char_id, day_index=1, event_id=event_id
    ).first()
    assert act is not None
    assert act.status_code == 1
    
    # Update status
    controller.update_daily_status(char_id, day=1, status=-1, event_id=event_id)
    test_db.refresh(act)
    assert act.status_code == -1

def test_tombola_dashboard_data(tombola_ctrl, test_db, seed_data):
    """Test retrieving tombola dashboard data."""
    controller = tombola_ctrl
    
    server_id = seed_data['server'].id
    char_id = seed_data['character'].id
    event = controller.create_tombola_event(server_id, "Dash Event")
    
    # Setup Data
    controller.update_daily_status(char_id, 1, 1, event.id)
    
    # Query
    data = controller.get_tombola_dashboard_data(server_id, event.id)
    
    assert len(data) > 0
    store_entry = data[0]
    accounts = store_entry['accounts']
    game_acc = accounts[0]
    
    assert hasattr(game_acc, 'current_event_activity')
    assert game_acc.current_event_activity[1] == 1
