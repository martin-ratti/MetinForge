import pytest
from app.application.services.alchemy_service import AlchemyService

class MockAlchemyController(AlchemyService):
    def __init__(self, session):
        self.session = session
    def get_session(self):
        return self.session

def test_full_alchemy_workflow(test_db, seed_data):
    """
    Simulate a user workflow:
    1. Open Alchemy View (controller init)
    2. Check status (empty)
    3. Mark Day 1 as Done
    4. Mark Day 2 as Done
    5. Check integrity
    """
    controller = MockAlchemyController(test_db)
    char_id = seed_data['character'].id
    event_id = 1
    
    # 1. Check initial state
    matrix = get_character_matrix_helper(controller, char_id, event_id, 30)
    assert matrix[1] == 0 # Day 1 is pending
    
    # 2. Update Day 1 -> Done (1)
    controller.update_daily_status(char_id, 1, 1, event_id)
    matrix = get_character_matrix_helper(controller, char_id, event_id, 30)
    assert matrix[1] == 1
    
    # 3. Update Day 2 -> Done (1)
    controller.update_daily_status(char_id, 2, 1, event_id)
    matrix = get_character_matrix_helper(controller, char_id, event_id, 30)
    assert matrix[2] == 1
    
    # 4. Update Day 1 -> Failed (-1) (Correction)
    controller.update_daily_status(char_id, 1, -1, event_id)
    matrix = get_character_matrix_helper(controller, char_id, event_id, 30)
    assert matrix[1] == -1
    assert matrix[2] == 1 # Day 2 should remain untouched

def get_character_matrix_helper(controller, char_id, event_id, total_days):
    from app.domain.models import DailyCorActivity
    session = controller.get_session()
    activities = session.query(DailyCorActivity).filter_by(
        character_id=char_id,
        event_id=event_id
    ).all()
    
    # Defaults
    matrix = {d: 0 for d in range(1, total_days + 1)}
    for act in activities:
        matrix[act.day_index] = act.status_code
    return matrix
