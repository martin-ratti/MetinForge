import pytest
from unittest.mock import MagicMock, patch
from app.application.services.base_service import BaseService

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def service(mock_session):
    svc = BaseService(session=mock_session)
    return svc


def test_get_session_injected(service, mock_session):
    """Con session inyectada, retorna la misma."""
    assert service.get_session() == mock_session


def test_get_session_creates_new():
    """Sin session inyectada, crea una nueva."""
    with patch('app.application.services.base_service.create_engine') as mock_engine, \
         patch('app.application.services.base_service.sessionmaker') as mock_maker:
        svc = BaseService()
        session = svc.get_session()
        mock_maker.assert_called_once()


def test_get_next_pending_day_no_event(service):
    """Sin event_id, retorna 1 (por exception handling)."""
    result = service._get_next_pending_day_generic(char_id=1, event_id=None, activity_model=MagicMock())
    assert result >= 1


def test_get_next_pending_day_no_activities(service, mock_session):
    """Sin actividades, retorna dia 1."""
    mock_session.query.return_value.filter_by.return_value.all.return_value = []
    result = service._get_next_pending_day_generic(char_id=1, event_id=1, activity_model=MagicMock())
    assert result == 1


def test_get_next_pending_day_first_done(service, mock_session):
    """Dia 1 completado, retorna dia 2."""
    act = MagicMock(day_index=1, status_code=1)
    mock_session.query.return_value.filter_by.return_value.all.return_value = [act]
    result = service._get_next_pending_day_generic(char_id=1, event_id=1, activity_model=MagicMock())
    assert result == 2


def test_get_next_pending_day_gap(service, mock_session):
    """Dia 1 y 3 completados, retorna dia 2 (gap)."""
    act1 = MagicMock(day_index=1, status_code=1)
    act3 = MagicMock(day_index=3, status_code=1)
    mock_session.query.return_value.filter_by.return_value.all.return_value = [act1, act3]
    result = service._get_next_pending_day_generic(char_id=1, event_id=1, activity_model=MagicMock())
    assert result == 2


def test_get_next_pending_day_all_done(service, mock_session):
    """Todos los dias completados, retorna max_days."""
    activities = [MagicMock(day_index=i, status_code=1) for i in range(1, 32)]
    mock_session.query.return_value.filter_by.return_value.all.return_value = activities
    result = service._get_next_pending_day_generic(char_id=1, event_id=1, activity_model=MagicMock(), max_days=31)
    assert result == 31
