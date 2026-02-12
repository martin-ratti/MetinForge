"""
Tests de integración para Tombola: flujos CRUD completos, eventos y gestión de premios.
"""
import pytest
from app.application.services.tombola_service import TombolaService
from app.domain.models import TombolaActivity, TombolaEvent, TombolaItemCounter

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

@pytest.fixture
def tombola_ctrl(test_db):
    return MockTombolaService(test_db)

class TestTombolaIntegration:
    """Flujo completo de tombola: crear evento, counters, status diario."""

    def test_create_event_and_counters(self, tombola_ctrl, test_db, seed_data):
        server_id = seed_data["server"].id
        
        event = tombola_ctrl.create_tombola_event(server_id, "Tombola Integration")
        assert event is not None
        assert event.name == "Tombola Integration"
        
        result = tombola_ctrl.update_tombola_item_count(event.id, "Piedra", 5)
        assert result is True
        
        counters = tombola_ctrl.get_tombola_item_counters(event.id)
        assert counters["Piedra"] == 5

    def test_update_counter_value(self, tombola_ctrl, test_db, seed_data):
        event = tombola_ctrl.create_tombola_event(seed_data["server"].id, "Counter Update")
        tombola_ctrl.update_tombola_item_count(event.id, "Gema", 3)
        tombola_ctrl.update_tombola_item_count(event.id, "Gema", 10)
        
        counters = tombola_ctrl.get_tombola_item_counters(event.id)
        assert counters["Gema"] == 10

    def test_daily_status_flow(self, tombola_ctrl, test_db, seed_data):
        char_id = seed_data["character"].id
        event = tombola_ctrl.create_tombola_event(seed_data["server"].id, "Daily Flow")
        
        tombola_ctrl.update_daily_status(char_id, 1, 1, event.id)
        
        activity = test_db.query(TombolaActivity).filter_by(
            character_id=char_id, event_id=event.id, day_index=1
        ).first()
        assert activity is not None
        assert activity.status_code == 1

    def test_get_events(self, tombola_ctrl, test_db, seed_data):
        server_id = seed_data["server"].id
        tombola_ctrl.create_tombola_event(server_id, "Evento1")
        tombola_ctrl.create_tombola_event(server_id, "Evento2")
        
        events = tombola_ctrl.get_tombola_events(server_id)
        assert len(events) >= 2

    def test_tombola_dashboard_data(self, tombola_ctrl, test_db, seed_data):
        server_id = seed_data['server'].id
        char_id = seed_data['character'].id
        event = tombola_ctrl.create_tombola_event(server_id, "Dash Event")
        
        tombola_ctrl.update_daily_status(char_id, 1, 1, event.id)
        
        data = tombola_ctrl.get_tombola_dashboard_data(server_id, event.id)
        assert len(data) > 0
        game_acc = data[0]['accounts'][0]
        assert game_acc.current_event_activity[1] == 1
