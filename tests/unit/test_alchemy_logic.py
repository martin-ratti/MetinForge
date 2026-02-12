import pytest
from unittest.mock import MagicMock, patch
from app.application.services.alchemy_service import AlchemyService
from app.domain.models import DailyCorActivity

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def controller(mock_session):
    with patch('app.application.services.base_service.create_engine'), \
         patch('app.application.services.base_service.sessionmaker'):
        ctrl = AlchemyService()
        ctrl.get_session = MagicMock(return_value=mock_session)
        return ctrl

def test_get_next_pending_day_no_event(controller):
    assert controller.get_next_pending_day(1, None) == 1

def test_get_next_pending_day_no_activities(controller, mock_session):
    mock_session.query.return_value.filter_by.return_value.all.return_value = []
    assert controller.get_next_pending_day(1, 1) == 1

def test_get_next_pending_day_first_day_pending(controller, mock_session):
    act = MagicMock()
    act.day_index = 1
    act.status_code = 0
    mock_session.query.return_value.filter_by.return_value.all.return_value = [act]
    assert controller.get_next_pending_day(1, 1) == 1

def test_get_next_pending_day_first_day_completed(controller, mock_session):
    act = MagicMock()
    act.day_index = 1
    act.status_code = 1
    mock_session.query.return_value.filter_by.return_value.all.return_value = [act]
    assert controller.get_next_pending_day(1, 1) == 2

def test_get_next_pending_day_gap(controller, mock_session):
    act1 = MagicMock(day_index=1, status_code=1)
    act3 = MagicMock(day_index=3, status_code=1)
    mock_session.query.return_value.filter_by.return_value.all.return_value = [act1, act3]
    assert controller.get_next_pending_day(1, 1) == 2
