"""
Tests de integración para Alchemy: flujos CRUD completos, workflow de usuario y gestión de eventos.
Fusionado de test_integration_services.py, test_alchemy_full.py y test_workflow.py
"""
import pytest
from app.application.services.alchemy_service import AlchemyService
from app.domain.models import (
    Server, StoreAccount, GameAccount, Character, 
    AlchemyEvent, DailyCorActivity
)

class SessionProxy:
    """Proxy que delega todo a la sesión de SQLAlchemy excepto close()."""
    def __init__(self, session):
        self._session = session
    def __getattr__(self, name):
        if name == 'close':
            return lambda: None
        return getattr(self._session, name)

class MockAlchemyService(AlchemyService):
    def __init__(self, session):
        self._proxy = SessionProxy(session)
        super().__init__(session=self._proxy)
        self._test_session = self._proxy
    def Session(self):
        return self._test_session

@pytest.fixture
def alchemy_ctrl(test_db):
    return MockAlchemyService(test_db)

# =================== TESTS DE INTEGRACION (Servicio) ===================

class TestAlchemyServiceIntegration:
    """Tests para AlchemyService con BD real SQLite in-memory."""

    def test_create_server_and_event(self, alchemy_ctrl, test_db):
        server = Server(name="IntegrationServer")
        test_db.add(server)
        test_db.commit()
        
        events = alchemy_ctrl.get_alchemy_events(server.id)
        assert len(events) == 0
        
        event = alchemy_ctrl.create_alchemy_event(server.id, "Evento Test", 30)
        assert event is not None
        assert event.name == "Evento Test"
        
        events = alchemy_ctrl.get_alchemy_events(server.id)
        assert len(events) == 1

    def test_daily_status_flow(self, alchemy_ctrl, test_db, seed_data):
        char_id = seed_data["character"].id
        event = AlchemyEvent(server_id=seed_data["server"].id, name="DailyFlow", total_days=30)
        test_db.add(event)
        test_db.commit()
        event_id = event.id
        
        alchemy_ctrl.update_daily_status(char_id, 1, 1, event_id)
        
        activities = test_db.query(DailyCorActivity).filter_by(
            character_id=char_id, event_id=event_id
        ).all()
        assert len(activities) == 1
        assert activities[0].status_code == 1
        
        alchemy_ctrl.update_daily_status(char_id, 1, -1, event_id)
        test_db.expire_all()
        activities = test_db.query(DailyCorActivity).filter_by(
            character_id=char_id, event_id=event_id
        ).all()
        assert activities[0].status_code == -1

    def test_next_pending_day(self, alchemy_ctrl, test_db, seed_data):
        char_id = seed_data["character"].id
        event = AlchemyEvent(server_id=seed_data["server"].id, name="PendingFlow", total_days=30)
        test_db.add(event)
        test_db.commit()
        event_id = event.id
        
        assert alchemy_ctrl.get_next_pending_day(char_id, event_id) == 1
        
        alchemy_ctrl.update_daily_status(char_id, 1, 1, event_id)
        assert alchemy_ctrl.get_next_pending_day(char_id, event_id) == 2

# =================== TESTS DE GESTION DE CUENTAS ===================

class TestAlchemyAccountManagement:
    """Tests para gestion de servidores, tiendas y cuentas desde el servicio."""

    def test_server_management(self, alchemy_ctrl, test_db):
        success = alchemy_ctrl.create_server("NewServer", flags={'dailies': True})
        assert success is True
        
        server = test_db.query(Server).filter_by(name="NewServer").first()
        assert server is not None
        assert server.has_dailies is True
        
        flags = alchemy_ctrl.get_server_flags(server.id)
        assert flags['has_dailies'] is True
        
        success = alchemy_ctrl.update_server_feature(server.id, "fishing", True)
        assert success is True
        test_db.refresh(server)
        assert server.has_fishing is True

    def test_account_creation_chain(self, alchemy_ctrl, test_db, seed_data):
        success = alchemy_ctrl.create_store_email("newstore@gmail.com")
        assert success is True
        store = test_db.query(StoreAccount).filter_by(email="newstore@gmail.com").first()
        assert store is not None
        
        server_id = seed_data['server'].id
        success = alchemy_ctrl.create_game_account(
            server_id=server_id,
            username="NewGameAcc",
            store_email="newstore@gmail.com"
        )
        assert success is True
        game_acc = test_db.query(GameAccount).filter_by(username="NewGameAcc").first()
        assert game_acc is not None
        assert game_acc.store_account_id == store.id
        assert len(game_acc.characters) == 5

# =================== TESTS DE WORKFLOW DE USUARIO ===================

def test_full_alchemy_workflow(alchemy_ctrl, test_db, seed_data):
    """Simula un flujo de usuario real: verificar pendiente -> completar -> verificar."""
    char_id = seed_data['character'].id
    event = AlchemyEvent(server_id=seed_data['server'].id, name="Workflow", total_days=30)
    test_db.add(event)
    test_db.commit()
    event_id = event.id
    
    # 1. Dia 1 pendiente
    assert alchemy_ctrl.get_next_pending_day(char_id, event_id) == 1
    
    # 2. Completar Dia 1
    alchemy_ctrl.update_daily_status(char_id, 1, 1, event_id)
    assert alchemy_ctrl.get_next_pending_day(char_id, event_id) == 2
    
    # 3. Completar Dia 2
    alchemy_ctrl.update_daily_status(char_id, 2, 1, event_id)
    assert alchemy_ctrl.get_next_pending_day(char_id, event_id) == 3
    
    # 4. Corregir Dia 1 a Fallido
    alchemy_ctrl.update_daily_status(char_id, 1, -1, event_id)
    # Sigue pendiente el dia 3 porque el 1 tiene registro (aunque sea fallido)
    # Bueno, segun la logica de get_next_pending_day: "if status_map.get(day, 0) == 0: return day"
    # Status -1 != 0, asi que el 1 ya no esta "pendiente" en el sentido de "no intentado".
    assert alchemy_ctrl.get_next_pending_day(char_id, event_id) == 3

def test_daily_cords_records(alchemy_ctrl, test_db, seed_data):
    """Test para registros de fragments (Cords)."""
    game_acc_id = seed_data['game_account'].id
    event = alchemy_ctrl.create_alchemy_event(seed_data['server'].id, "Cords Event", 30)
    event_id = event.id
    
    success = alchemy_ctrl.update_daily_cords(game_acc_id, event_id, 1, 15)
    assert success is True
    
    cords_map = alchemy_ctrl.get_daily_cords(game_acc_id, event_id)
    assert cords_map[1] == 15
    
    assert alchemy_ctrl.get_total_cords(game_acc_id, event_id) == 15
