import pytest
from unittest.mock import MagicMock, patch
from app.application.services.fishing_service import FishingService
from app.application.dtos import StoreAccountDTO, GameAccountDTO, CharacterDTO
from app.domain.models import StoreAccount, GameAccount, FishingActivity

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def service(mock_session):
    with patch('app.application.services.base_service.create_engine'), \
         patch('app.application.services.base_service.sessionmaker'):
        svc = FishingService()
        svc.get_session = MagicMock(return_value=mock_session)
        return svc


def test_get_fishing_data_empty(service, mock_session):
    """Sin tiendas, retorna lista vacia."""
    mock_session.query.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = []
    result = service.get_fishing_data(server_id=1, year=2026)
    assert result == []


def test_get_fishing_data_returns_dtos(service, mock_session):
    """Verifica que se retornen objetos DTO correctamente estructurados."""
    # Mock data
    store = MagicMock(spec=StoreAccount)
    store.id = 1
    store.email = "test@mail.com"
    
    ga = MagicMock(spec=GameAccount)
    ga.id = 10
    ga.username = "user1"
    ga.server_id = 1
    ga.store_account_id = 1
    
    char = MagicMock()
    char.id = 100
    char.name = "Fisher"
    char.job = 1
    char.level = 10
    ga.characters = [char]
    
    # Configure mock query side effects
    def query_side_effect(model):
        query_mock = MagicMock()
        if model == StoreAccount:
            query_mock.join.return_value.filter.return_value.distinct.return_value.all.return_value = [store]
        elif model == GameAccount:
            query_mock.filter.return_value.all.return_value = [ga]
        elif model == FishingActivity:
            act = MagicMock()
            act.month = 1
            act.week = 1
            act.status_code = 1
            query_mock.filter.return_value.all.return_value = [act]
        return query_mock

    mock_session.query.side_effect = query_side_effect
    
    result = service.get_fishing_data(server_id=1, year=2026)
    
    assert len(result) == 1
    assert isinstance(result[0], StoreAccountDTO)
    assert result[0].email == "test@mail.com"
    
    assert len(result[0].game_accounts) == 1
    ga_dto = result[0].game_accounts[0]
    assert isinstance(ga_dto, GameAccountDTO)
    assert ga_dto.username == "user1"
    
    assert len(ga_dto.characters) == 1
    char_dto = ga_dto.characters[0]
    assert isinstance(char_dto, CharacterDTO)
    assert char_dto.name == "Fisher"
    
    # Check activity map
    assert char_dto.fishing_activity_map.get("1_1") == 1


def test_get_last_filled_week_no_activity(service, mock_session):
    """Sin actividad, retorna (None, None)."""
    mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    m, w = service.get_last_filled_week(char_id=1, year=2026)
    assert m is None
    assert w is None


def test_get_last_filled_week_with_activity(service, mock_session):
    """Con actividad, retorna (month, week) del ultimo registro."""
    act = MagicMock()
    act.month = 5
    act.week = 3
    mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = act
    m, w = service.get_last_filled_week(char_id=1, year=2026)
    assert m == 5
    assert w == 3


def test_get_next_pending_week_no_activities(service, mock_session):
    """Sin actividades, el primer pendiente es (1, 1)."""
    mock_session.query.return_value.filter_by.return_value.all.return_value = []
    m, w = service.get_next_pending_week(char_id=1, year=2026)
    assert m == 1
    assert w == 1


def test_get_next_pending_week_partial(service, mock_session):
    """Con actividades parciales, retorna el proximo pendiente."""
    act1 = MagicMock(month=1, week=1, status_code=1)
    act2 = MagicMock(month=1, week=2, status_code=1)
    mock_session.query.return_value.filter_by.return_value.all.return_value = [act1, act2]
    m, w = service.get_next_pending_week(char_id=1, year=2026)
    assert m == 1
    assert w == 3


def test_update_fishing_status_new(service, mock_session):
    """Crear nueva actividad cuando no existe."""
    mock_session.query.return_value.filter.return_value.first.return_value = None
    result = service.update_fishing_status(char_id=1, year=2026, month=3, week=2, new_status=1)
    assert result is True
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_update_fishing_status_existing(service, mock_session):
    """Actualizar actividad existente."""
    existing = MagicMock()
    existing.status_code = 0
    mock_session.query.return_value.filter.return_value.first.return_value = existing
    result = service.update_fishing_status(char_id=1, year=2026, month=3, week=2, new_status=1)
    assert result is True
    assert existing.status_code == 1
    mock_session.commit.assert_called_once()


def test_update_fishing_status_error(service, mock_session):
    """Error en update retorna False."""
    mock_session.query.return_value.filter.return_value.first.side_effect = Exception("DB error")
    result = service.update_fishing_status(char_id=1, year=2026, month=1, week=1, new_status=1)
    assert result is False
    mock_session.rollback.assert_called_once()


def test_bulk_import_accounts_empty_data(service):
    """Datos vacios retorna 0."""
    result = service.bulk_import_accounts(server_id=1, import_data={"email": "", "characters": []})
    assert result == 0


def test_bulk_import_accounts_list(service, mock_session):
    """Importacion con lista de dicts."""
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    mock_session.flush = MagicMock()
    
    data = [
        {"email": "test@mail.com", "characters": [{"name": "Fisher1", "slots": 5}]},
    ]
    result = service.bulk_import_accounts(server_id=1, import_data=data)
    assert result >= 0
