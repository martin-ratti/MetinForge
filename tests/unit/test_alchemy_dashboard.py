import pytest
from unittest.mock import MagicMock, patch
from app.controllers.alchemy_controller import AlchemyController
from app.models.models import StoreAccount, GameAccount, Character, DailyCorActivity

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def controller(mock_session):
    with patch('app.controllers.base_controller.create_engine'), \
         patch('app.controllers.base_controller.sessionmaker'):
        ctrl = AlchemyController()
        ctrl.get_session = MagicMock(return_value=mock_session) # Use get_session returning mock
        ctrl.Session = MagicMock(return_value=mock_session) # Keep this for legacy calls if any
        return ctrl

def test_get_alchemy_dashboard_data_empty(controller, mock_session):
    # Setup
    mock_session.query.return_value.options.return_value.filter.return_value.all.return_value = []
    
    # Execute
    result = controller.get_alchemy_dashboard_data(server_id=1, event_id=1)
    
    # Verify
    assert result == []

def test_get_alchemy_dashboard_data_with_data(controller, mock_session):
    # Setup Data
    char = MagicMock(spec=Character)
    char.id = 101
    
    game_acc = MagicMock(spec=GameAccount)
    game_acc.id = 10
    game_acc.server_id = 1
    game_acc.characters = [char]
    
    store = MagicMock(spec=StoreAccount)
    store.id = 1
    store.game_accounts = [game_acc]
    
    # Mock query result for Stores
    # chain: session.query(Store).options().filter().all()
    mock_session.query.return_value.options.return_value.filter.return_value.all.return_value = [store]
    
    # Mock query result for Activities
    activity = MagicMock(spec=DailyCorActivity)
    activity.character_id = 101
    activity.day_index = 5
    activity.status_code = 1
    activity.event_id = 99
    
    # chain: session.query(Activity).filter().all()
    # The controller calls session.query(DailyCorActivity) secondary
    # We need to handle multiple queries.
    # First query is StoreAccount. Second is DailyCorActivity.
    
    # Define side effect for session.query
    def query_side_effect(model):
        m = MagicMock()
        if model == StoreAccount:
             # Return mock that leads to [store]
             m.options.return_value.filter.return_value.all.return_value = [store]
             # Handle filter(StoreAccount.email == ...) if needed
             m.options.return_value.filter.return_value.filter.return_value.all.return_value = [store]
             return m
        elif model == DailyCorActivity:
             m.filter.return_value.all.return_value = [activity]
             return m
        return m

    mock_session.query.side_effect = query_side_effect
    
    # Execute
    result = controller.get_alchemy_dashboard_data(server_id=1, event_id=99)
    
    # Verify Structure
    assert len(result) == 1
    assert result[0]['store'] == store
    assert len(result[0]['accounts']) == 1
    
    acc_result = result[0]['accounts'][0]
    assert acc_result == game_acc
    assert hasattr(acc_result, 'current_event_activity')
    assert acc_result.current_event_activity == {5: 1} # Char 101, Day 5, Status 1
