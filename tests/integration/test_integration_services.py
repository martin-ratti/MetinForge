"""
Tests de integracion para servicios con BD SQLite in-memory.
Verifican flujos CRUD completos sin mocks.
"""
import pytest
from app.application.services.alchemy_service import AlchemyService
from app.application.services.fishing_service import FishingService
from app.application.services.tombola_service import TombolaService
from app.domain.models import (
    Server, StoreAccount, GameAccount, Character, CharacterType,
    AlchemyEvent, DailyCorActivity, FishingActivity,
    TombolaEvent, TombolaActivity, TombolaItemCounter
)


class MockAlchemyService(AlchemyService):
    """Mock que inyecta session de test. Overrides Session() para create_alchemy_event."""
    def __init__(self, session):
        super().__init__(session=session)
        self._test_session = session
    def Session(self):
        return self._test_session


class MockFishingService(FishingService):
    def __init__(self, session):
        super().__init__(session=session)


class MockTombolaService(TombolaService):
    def __init__(self, session):
        super().__init__(session=session)


# =================== ALCHEMY ===================

class TestAlchemyIntegration:
    """Flujo completo de alchemy: crear server, evento, importar, actualizar."""

    def test_create_server_and_event(self, test_db):
        svc = MockAlchemyService(test_db)
        
        server = Server(name="IntegrationServer")
        test_db.add(server)
        test_db.commit()
        
        events = svc.get_alchemy_events(server.id)
        assert len(events) == 0
        
        event = svc.create_alchemy_event(server.id, "Evento Test", 30)
        assert event is not None
        assert event.name == "Evento Test"
        
        events = svc.get_alchemy_events(server.id)
        assert len(events) == 1

    def test_daily_status_flow(self, test_db, seed_data):
        svc = MockAlchemyService(test_db)
        char_id = seed_data["character"].id
        
        event = AlchemyEvent(server_id=seed_data["server"].id, name="DailyFlow", total_days=30)
        test_db.add(event)
        test_db.commit()
        event_id = event.id
        
        svc.update_daily_status(char_id, 1, 1, event_id)
        
        activities = test_db.query(DailyCorActivity).filter_by(
            character_id=char_id, event_id=event_id
        ).all()
        assert len(activities) == 1
        assert activities[0].status_code == 1
        
        svc.update_daily_status(char_id, 1, -1, event_id)
        test_db.expire_all()
        activities = test_db.query(DailyCorActivity).filter_by(
            character_id=char_id, event_id=event_id
        ).all()
        assert activities[0].status_code == -1

    def test_next_pending_day(self, test_db, seed_data):
        svc = MockAlchemyService(test_db)
        char_id = seed_data["character"].id
        
        event = AlchemyEvent(server_id=seed_data["server"].id, name="PendingFlow", total_days=30)
        test_db.add(event)
        test_db.commit()
        event_id = event.id
        
        next_day = svc.get_next_pending_day(char_id, event_id)
        assert next_day == 1
        
        svc.update_daily_status(char_id, 1, 1, event_id)
        next_day = svc.get_next_pending_day(char_id, event_id)
        assert next_day == 2


# =================== FISHING ===================

class TestFishingIntegration:
    """Flujo completo de fishing: crear, actualizar status, verificar pendientes."""

    def test_update_and_get_status(self, test_db, seed_data):
        svc = MockFishingService(test_db)
        char_id = seed_data["character"].id
        
        result = svc.update_fishing_status(char_id, 2026, 1, 1, 1)
        assert result is True
        
        activity = test_db.query(FishingActivity).filter_by(
            character_id=char_id, year=2026, month=1, week=1
        ).first()
        assert activity is not None
        assert activity.status_code == 1

    def test_update_existing_status(self, test_db, seed_data):
        svc = MockFishingService(test_db)
        char_id = seed_data["character"].id
        
        svc.update_fishing_status(char_id, 2026, 2, 1, 1)
        svc.update_fishing_status(char_id, 2026, 2, 1, -1)
        
        activity = test_db.query(FishingActivity).filter_by(
            character_id=char_id, year=2026, month=2, week=1
        ).first()
        assert activity.status_code == -1

    def test_last_filled_week(self, test_db, seed_data):
        svc = MockFishingService(test_db)
        char_id = seed_data["character"].id
        
        m, w = svc.get_last_filled_week(char_id, 2026)
        assert m is None
        assert w is None
        
        svc.update_fishing_status(char_id, 2026, 3, 2, 1)
        m, w = svc.get_last_filled_week(char_id, 2026)
        assert m == 3
        assert w == 2

    def test_next_pending_week(self, test_db, seed_data):
        svc = MockFishingService(test_db)
        char_id = seed_data["character"].id
        
        m, w = svc.get_next_pending_week(char_id, 2026)
        assert m == 1
        assert w == 1
        
        svc.update_fishing_status(char_id, 2026, 1, 1, 1)
        m, w = svc.get_next_pending_week(char_id, 2026)
        assert m == 1
        assert w == 2


# =================== TOMBOLA ===================

class TestTombolaIntegration:
    """Flujo completo de tombola: crear evento, counters, status diario."""

    def test_create_event_and_counters(self, test_db, seed_data):
        svc = MockTombolaService(test_db)
        server_id = seed_data["server"].id
        
        event = svc.create_tombola_event(server_id, "Tombola Integration")
        assert event is not None
        assert event.name == "Tombola Integration"
        
        result = svc.update_tombola_item_count(event.id, "Piedra", 5)
        assert result is True
        
        counters = svc.get_tombola_item_counters(event.id)
        assert counters["Piedra"] == 5

    def test_update_counter_value(self, test_db, seed_data):
        svc = MockTombolaService(test_db)
        
        event = svc.create_tombola_event(seed_data["server"].id, "Counter Update")
        svc.update_tombola_item_count(event.id, "Gema", 3)
        svc.update_tombola_item_count(event.id, "Gema", 10)
        
        counters = svc.get_tombola_item_counters(event.id)
        assert counters["Gema"] == 10

    def test_daily_status_flow(self, test_db, seed_data):
        svc = MockTombolaService(test_db)
        char_id = seed_data["character"].id
        
        event = svc.create_tombola_event(seed_data["server"].id, "Daily Flow")
        
        svc.update_daily_status(char_id, 1, 1, event.id)
        
        activity = test_db.query(TombolaActivity).filter_by(
            character_id=char_id, event_id=event.id, day_index=1
        ).first()
        assert activity is not None
        assert activity.status_code == 1

    def test_get_events(self, test_db, seed_data):
        svc = MockTombolaService(test_db)
        server_id = seed_data["server"].id
        
        svc.create_tombola_event(server_id, "Evento1")
        svc.create_tombola_event(server_id, "Evento2")
        
        events = svc.get_tombola_events(server_id)
        assert len(events) >= 2


# =================== CROSS-SERVICE ===================

class TestCrossServiceIntegration:
    """Verifica que un server funciona con multiples servicios simultáneamente."""

    def test_server_shared_between_services(self, test_db, seed_data):
        alchemy_svc = MockAlchemyService(test_db)
        tombola_svc = MockTombolaService(test_db)
        fishing_svc = MockFishingService(test_db)
        
        server_id = seed_data["server"].id
        char_id = seed_data["character"].id
        
        alch_event = AlchemyEvent(server_id=server_id, name="Shared Alchemy", total_days=30)
        test_db.add(alch_event)
        test_db.commit()
        alch_event_id = alch_event.id
        
        tomb_event = tombola_svc.create_tombola_event(server_id, "Shared Tombola")
        tomb_event_id = tomb_event.id
        
        alchemy_svc.update_daily_status(char_id, 1, 1, alch_event_id)
        tombola_svc.update_daily_status(char_id, 1, 1, tomb_event_id)
        fishing_svc.update_fishing_status(char_id, 2026, 1, 1, 1)
        
        alch_acts = test_db.query(DailyCorActivity).filter_by(character_id=char_id).count()
        tomb_acts = test_db.query(TombolaActivity).filter_by(character_id=char_id).count()
        fish_acts = test_db.query(FishingActivity).filter_by(character_id=char_id).count()
        
        assert alch_acts >= 1
        assert tomb_acts >= 1
        assert fish_acts >= 1
