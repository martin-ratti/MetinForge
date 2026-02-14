"""
Tests de integración para Fishing: flujos CRUD completos y lógica de semanas pendientes.
"""
import pytest
from app.application.services.fishing_service import FishingService
from app.domain.models import FishingActivity, Character

class SessionProxy:
    """Proxy que delega todo a la sesión de SQLAlchemy excepto close()."""
    def __init__(self, session):
        self._session = session
    def __getattr__(self, name):
        if name == 'close':
            return lambda: None
        return getattr(self._session, name)

class MockFishingService(FishingService):
    def __init__(self, session):
        self._proxy = SessionProxy(session)
        super().__init__(session=self._proxy)

@pytest.fixture
def fishing_ctrl(test_db):
    return MockFishingService(test_db)

class TestFishingIntegration:
    """Flujo completo de fishing: crear, actualizar status, verificar pendientes."""

    def test_update_and_get_status(self, fishing_ctrl, test_db, seed_data):
        char_id = seed_data["character"].id
        
        result = fishing_ctrl.update_fishing_status(char_id, 2026, 1, 1, 1)
        assert result is True
        
        activity = test_db.query(FishingActivity).filter_by(
            character_id=char_id, year=2026, month=1, week=1
        ).first()
        assert activity is not None
        assert activity.status_code == 1

    def test_update_existing_status(self, fishing_ctrl, test_db, seed_data):
        char_id = seed_data["character"].id
        
        fishing_ctrl.update_fishing_status(char_id, 2026, 2, 1, 1)
        fishing_ctrl.update_fishing_status(char_id, 2026, 2, 1, -1)
        
        test_db.expire_all()
        activity = test_db.query(FishingActivity).filter_by(
            character_id=char_id, year=2026, month=2, week=1
        ).first()
        assert activity.status_code == -1

    def test_last_filled_week(self, fishing_ctrl, test_db, seed_data):
        char_id = seed_data["character"].id
        
        m, w = fishing_ctrl.get_last_filled_week(char_id, 2026)
        assert m is None
        assert w is None
        
        fishing_ctrl.update_fishing_status(char_id, 2026, 3, 2, 1)
        m, w = fishing_ctrl.get_last_filled_week(char_id, 2026)
        assert m == 3
        assert w == 2

    def test_next_pending_week(self, fishing_ctrl, test_db, seed_data):
        char_id = seed_data["character"].id
        
        m, w = fishing_ctrl.get_next_pending_week(char_id, 2026)
        assert (m, w) == (1, 1)
        
        fishing_ctrl.update_fishing_status(char_id, 2026, 1, 1, 1)
        m, w = fishing_ctrl.get_next_pending_week(char_id, 2026)
        assert (m, w) == (1, 2)

    def test_get_fishing_data(self, fishing_ctrl, test_db, seed_data):
        """Test retrieving fishing dashboard data."""
        server_id = seed_data['server'].id
        char_id = seed_data['character'].id
        year = 2026
        
        fishing_ctrl.update_fishing_status(char_id, year, 1, 1, 1)
        fishing_ctrl.update_fishing_status(char_id, year, 1, 2, -1)
        
        data = fishing_ctrl.get_fishing_data(server_id, year)
        
        assert len(data) > 0
        store_dto = data[0]
        game_acc_dto = store_dto.game_accounts[0]
        char_dto = game_acc_dto.characters[0]
        
        assert char_dto.fishing_activity_map['1_1'] == 1
        assert char_dto.fishing_activity_map['1_2'] == -1
