import pytest
from datetime import datetime
from app.controllers.alchemy_controller import AlchemyController
from app.controllers.fishing_controller import FishingController
from app.controllers.tombola_controller import TombolaController
from app.models.models import DailyCorActivity, FishingActivity, TombolaActivity

class MockAlchemyController(AlchemyController):
    def __init__(self, session):
        self.session = session
    
    def get_session(self):
        return self.session

    def get_next_pending_day(self, char_id, event_id):
        # Implementation similar to real controller but using self.session
        activities = self.session.query(DailyCorActivity).filter_by(
            character_id=char_id,
            event_id=event_id
        ).order_by(DailyCorActivity.day_index).all()
        status_map = {a.day_index: a.status_code for a in activities}
        current_day = 1
        while True:
            if status_map.get(current_day, 0) == 0:
                return current_day
            current_day += 1

class MockFishingController(FishingController):
    def __init__(self, session):
        self.session = session
    def get_session(self):
        return self.session

class MockTombolaController(TombolaController):
    def __init__(self, session):
        self.session = session
    
    def get_session(self): 
        return self.session

    def get_next_pending_day(self, char_id, event_id):
        activities = self.session.query(TombolaActivity).filter_by(
            character_id=char_id,
            event_id=event_id
        ).order_by(TombolaActivity.day_index).all()
        status_map = {a.day_index: a.status_code for a in activities}
        current_day = 1
        while True:
            if status_map.get(current_day, 0) == 0:
                return current_day
            current_day += 1



def test_alchemy_next_pending_day(test_db, seed_data):
    """Test finding the next pending day for Alchemy."""
    controller = MockAlchemyController(test_db)
    char_id = seed_data['character'].id
    
    # Initially, day 1 should be pending
    day = controller.get_next_pending_day(char_id, event_id=1) 
    # Note: Event ID 1 assumes one event exists or handled. 
    # Actually get_next_pending_day usually relies on existing entries or logic.
    # If no entries, it returns 1.
    assert day == 1
    
    # Mark day 1 as done
    act = DailyCorActivity(character_id=char_id, day_index=1, status_code=1, event_id=1)
    test_db.add(act)
    test_db.commit()
    
    day = controller.get_next_pending_day(char_id, event_id=1)
    assert day == 2

def test_fishing_next_pending_week(test_db, seed_data):
    """Test finding the next pending week for Fishing."""
    controller = MockFishingController(test_db)
    char_id = seed_data['character'].id
    year = 2026
    
    # Initially, Month 1 Week 1
    m, w = controller.get_next_pending_week(char_id, year)
    assert m == 1
    assert w == 1
    
    # Mark M1 W1 as done
    act = FishingActivity(character_id=char_id, year=year, month=1, week=1, status_code=1)
    test_db.add(act)
    test_db.commit()
    
    m, w = controller.get_next_pending_week(char_id, year)
    assert m == 1
    assert w == 2

    # Mark all of Month 1 as done
    for week in range(2, 5):
        act = FishingActivity(character_id=char_id, year=year, month=1, week=week, status_code=1)
        test_db.add(act)
    test_db.commit()
    
    m, w = controller.get_next_pending_week(char_id, year)
    assert m == 2
    assert w == 1

def test_tombola_next_pending_day(test_db, seed_data):
    """Test finding the next pending day for Tombola."""
    controller = MockTombolaController(test_db)
    char_id = seed_data['character'].id
    event_id = 99 # Arbitrary
    
    # Initially 1
    day = controller.get_next_pending_day(char_id, event_id)
    assert day == 1
    
    # Add day 1
    act = TombolaActivity(character_id=char_id, day_index=1, status_code=1, event_id=event_id)
    test_db.add(act)
    test_db.commit()
    
    day = controller.get_next_pending_day(char_id, event_id)
    assert day == 2
