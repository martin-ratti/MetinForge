import pytest
from app.application.services.fishing_service import FishingService
from app.domain.models import FishingActivity, StoreAccount, GameAccount, Character, CharacterType, Server

@pytest.fixture
def fishing_ctrl(test_db):
    ctrl = FishingService()
    class SessionProxy:
        def __init__(self, session): self._session = session
        def __getattr__(self, name):
            if name == 'close': return lambda: None
            return getattr(self._session, name)
    
    proxy = SessionProxy(test_db)
    ctrl.get_session = lambda: proxy
    return ctrl

def test_fishing_status_update(fishing_ctrl, test_db, seed_data):
    """Test updating fishing status for a character."""
    # Use fixture
    controller = fishing_ctrl
    
    char_id = seed_data['character'].id
    year = 2026
    month = 1
    week = 1
    
    # 1. Create new status
    success = controller.update_fishing_status(char_id, year, month, week, 1)
    assert success is True
    
    activity = test_db.query(FishingActivity).filter_by(
        character_id=char_id, year=year, month=month, week=week
    ).first()
    assert activity is not None
    assert activity.status_code == 1
    
    # 2. Update existing status
    success = controller.update_fishing_status(char_id, year, month, week, -1)
    assert success is True
    
    test_db.refresh(activity)
    assert activity.status_code == -1

def test_get_fishing_data(fishing_ctrl, test_db, seed_data):
    """Test retrieving fishing dashboard data."""
    controller = fishing_ctrl
    
    server_id = seed_data['server'].id
    char_id = seed_data['character'].id
    year = 2026
    
    # Setup some data
    act1 = FishingActivity(character_id=char_id, year=year, month=1, week=1, status_code=1)
    act2 = FishingActivity(character_id=char_id, year=year, month=1, week=2, status_code=-1)
    test_db.add_all([act1, act2])
    test_db.commit()
    
    # Retrieve data
    data = controller.get_fishing_data(server_id, year)
    
    assert len(data) > 0
    store_entry = data[0]
    assert store_entry['store'].id == seed_data['store'].id
    assert len(store_entry['accounts']) > 0
    
    game_acc = store_entry['accounts'][0]
    assert game_acc.id == seed_data['game_account'].id
    
    # Verify attached map
    assert hasattr(game_acc, 'fishing_activity_map')
    activity_map = game_acc.fishing_activity_map
    assert activity_map['1_1'] == 1
    assert activity_map['1_2'] == -1
    assert '1_3' not in activity_map

def test_get_next_pending_week_logic(fishing_ctrl, test_db, seed_data):
    """Test finding the next pending week."""
    controller = fishing_ctrl
    
    char_id = seed_data['character'].id
    year = 2026
    
    # Case 1: No activity -> 1, 1
    m, w = controller.get_next_pending_week(char_id, year)
    assert (m, w) == (1, 1)
    
    # Case 2: Week 1 done -> 1, 2
    act = FishingActivity(character_id=char_id, year=year, month=1, week=1, status_code=1)
    test_db.add(act)
    test_db.commit()
    
    m, w = controller.get_next_pending_week(char_id, year)
    assert (m, w) == (1, 2)
    
    # Case 3: Complete Month 1 -> 2, 1
    for i in range(2, 5):
        test_db.add(FishingActivity(character_id=char_id, year=year, month=1, week=i, status_code=1))
    test_db.commit()
    
    m, w = controller.get_next_pending_week(char_id, year)
    assert (m, w) == (2, 1)

def test_fishing_update_error_handling(test_db):
    """Test error handling during update."""
    controller = FishingService()
    # Force error by passing invalid session or constraint violation? 
    # Easiest is mocking commit to raise exception
    
    from unittest.mock import MagicMock
    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("DB Error")
    controller.get_session = lambda: mock_session
    
    success = controller.update_fishing_status(999, 2026, 1, 1, 1)
    assert success is False
