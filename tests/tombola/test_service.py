import pytest
from unittest.mock import MagicMock, patch
from app.application.services.tombola_service import TombolaService

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def service(mock_session):
    with patch('app.application.services.base_service.create_engine'), \
         patch('app.application.services.base_service.sessionmaker'):
        svc = TombolaService()
        svc.get_session = MagicMock(return_value=mock_session)
        return svc


def test_get_tombola_item_counters_no_event(service):
    """Sin event_id, retorna dict vacio."""
    result = service.get_tombola_item_counters(event_id=None)
    assert result == {}


def test_get_tombola_item_counters_ok(service, mock_session):
    """Con counters, retorna mapa nombre->cantidad."""
    counter1 = MagicMock()
    counter1.item_name = "Piedra"
    counter1.count = 5
    counter2 = MagicMock()
    counter2.item_name = "Gema"
    counter2.count = 3
    mock_session.query.return_value.filter_by.return_value.all.return_value = [counter1, counter2]
    
    result = service.get_tombola_item_counters(event_id=1)
    assert result["Piedra"] == 5
    assert result["Gema"] == 3


def test_update_tombola_item_count_no_event(service):
    """Sin event_id, retorna False."""
    result = service.update_tombola_item_count(event_id=None, item_name="Gema", count=5)
    assert result is False


def test_update_tombola_item_count_no_item_name(service):
    """Sin item_name, retorna False."""
    result = service.update_tombola_item_count(event_id=1, item_name=None, count=5)
    assert result is False


def test_update_tombola_item_count_create_new(service, mock_session):
    """Crea counter nuevo si no existe."""
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    result = service.update_tombola_item_count(event_id=1, item_name="Piedra", count=3)
    assert result is True
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_update_tombola_item_count_update_existing(service, mock_session):
    """Actualiza counter existente."""
    existing = MagicMock()
    existing.count = 2
    mock_session.query.return_value.filter_by.return_value.first.return_value = existing
    result = service.update_tombola_item_count(event_id=1, item_name="Piedra", count=5)
    assert result is True
    assert existing.count == 5


def test_create_tombola_event_empty_name(service):
    """Nombre vacio retorna None."""
    result = service.create_tombola_event(server_id=1, event_name="")
    assert result is None


def test_update_daily_status_creates_new(service, mock_session):
    """Crea nueva actividad si no existe (no retorna valor, solo no lanza excepcion)."""
    mock_session.query.return_value.filter.return_value.first.return_value = None
    service.update_daily_status(character_id=1, day=5, status=1, event_id=1)
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_update_daily_status_updates_existing(service, mock_session):
    """Actualiza actividad existente."""
    existing = MagicMock()
    existing.status_code = 0
    mock_session.query.return_value.filter.return_value.first.return_value = existing
    service.update_daily_status(character_id=1, day=5, status=1, event_id=1)
    assert existing.status_code == 1
    mock_session.commit.assert_called_once()


def test_update_daily_status_error(service, mock_session):
    """Error hace rollback sin lanzar excepcion."""
    mock_session.query.return_value.filter.return_value.first.side_effect = Exception("DB error")
    service.update_daily_status(character_id=1, day=1, status=1, event_id=1)
    mock_session.rollback.assert_called_once()
