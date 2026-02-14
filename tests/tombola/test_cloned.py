import pytest
from app.application.services.tombola_service import TombolaService
from app.domain.models import (
    Server, StoreAccount, GameAccount, Character, 
    TombolaEvent, TombolaActivity
)

class SessionProxy:
    """Proxy que delega todo a la sesión de SQLAlchemy excepto close()."""
    def __init__(self, session):
        self._session = session
    def __getattr__(self, name):
        if name == 'close':
            return lambda: None
        return getattr(self._session, name)

class MockTombolaService(TombolaService):
    def __init__(self, session):
        self._proxy = SessionProxy(session)
        super().__init__(session=self._proxy)
        self._test_session = self._proxy
    def Session(self):
        return self._test_session

@pytest.fixture
def tombola_ctrl(test_db):
    return MockTombolaService(test_db)

class TestTombolaIntegration:
    def test_tombola_dashboard_data_cloned(self, tombola_ctrl, test_db, seed_data):
        server_id = seed_data['server'].id
        char_id = seed_data['character'].id
        event = tombola_ctrl.create_tombola_event(server_id, "Cloned Event")
        
        tombola_ctrl.update_daily_status(char_id, 1, 1, event.id)
        
        data = tombola_ctrl.get_tombola_dashboard_data(server_id, event.id)
        assert len(data.store_accounts) > 0
        store_dto = data.store_accounts[0]
        game_acc_dto = store_dto.game_accounts[0]
        char_dto = game_acc_dto.characters[0]
        assert char_dto.daily_status_map[1] == 1
