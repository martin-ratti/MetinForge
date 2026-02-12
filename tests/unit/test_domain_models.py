import pytest
from app.domain.models import (
    Server, StoreAccount, GameAccount, Character, CharacterType,
    FishingActivity, AlchemyEvent, DailyCorActivity, TombolaEvent,
    TombolaActivity, TombolaItemCounter, TimerRecord, DailyCorRecord,
    AlchemyCounter
)


class TestCharacterType:
    def test_alchemist_value(self):
        assert CharacterType.ALCHEMIST.value == "alchemist"

    def test_fisherman_value(self):
        assert CharacterType.FISHERMAN.value == "fisherman"

    def test_enum_members(self):
        assert len(CharacterType) == 2


class TestServerModel:
    def test_tablename(self):
        assert Server.__tablename__ == 'servers'

    def test_default_feature_flags(self, test_db):
        server = Server(name="TestFlags")
        test_db.add(server)
        test_db.commit()
        assert server.has_dailies is True
        assert server.has_fishing is True
        assert server.has_tombola is True

    def test_unique_name(self, test_db):
        s1 = Server(name="UniqueServer")
        test_db.add(s1)
        test_db.commit()
        s2 = Server(name="UniqueServer")
        test_db.add(s2)
        with pytest.raises(Exception):
            test_db.commit()
        test_db.rollback()


class TestStoreAccountModel:
    def test_tablename(self):
        assert StoreAccount.__tablename__ == 'store_accounts'

    def test_create_store(self, test_db):
        store = StoreAccount(email="store@test.com")
        test_db.add(store)
        test_db.commit()
        assert store.id is not None
        assert store.email == "store@test.com"


class TestGameAccountModel:
    def test_tablename(self):
        assert GameAccount.__tablename__ == 'game_accounts'

    def test_relationships(self, test_db, seed_data):
        """Verifica relaciones: GameAccount -> Server, Store, Characters."""
        acc = seed_data["game_account"]
        assert acc.server_id == seed_data["server"].id
        assert acc.store_account_id == seed_data["store"].id


class TestCharacterModel:
    def test_tablename(self):
        assert Character.__tablename__ == 'characters'

    def test_default_slots(self, test_db, seed_data):
        char = seed_data["character"]
        assert char.slots == 5 or char.slots is None

    def test_default_type(self, test_db):
        server = Server(name="TypeTest")
        test_db.add(server)
        test_db.commit()
        store = StoreAccount(email="type@test.com")
        test_db.add(store)
        test_db.commit()
        acc = GameAccount(username="TypeTestAcc", store_account_id=store.id, server_id=server.id)
        test_db.add(acc)
        test_db.commit()
        char = Character(name="DefaultType", game_account_id=acc.id)
        test_db.add(char)
        test_db.commit()
        assert char.char_type == CharacterType.ALCHEMIST


class TestFishingActivityModel:
    def test_tablename(self):
        assert FishingActivity.__tablename__ == 'fishing_activities'

    def test_create_activity(self, test_db, seed_data):
        activity = FishingActivity(
            year=2026, month=1, week=1,
            status_code=1,
            character_id=seed_data["character"].id
        )
        test_db.add(activity)
        test_db.commit()
        assert activity.id is not None
        assert activity.year == 2026
        assert activity.month == 1
        assert activity.week == 1
        assert activity.status_code == 1


class TestAlchemyEventModel:
    def test_tablename(self):
        assert AlchemyEvent.__tablename__ == 'alchemy_events'

    def test_create_event(self, test_db, seed_data):
        event = AlchemyEvent(
            server_id=seed_data["server"].id,
            name="Evento Test",
            total_days=30
        )
        test_db.add(event)
        test_db.commit()
        assert event.id is not None
        assert event.total_days == 30


class TestDailyCorActivityModel:
    def test_tablename(self):
        assert DailyCorActivity.__tablename__ == 'daily_cor_activities'

    def test_create_activity(self, test_db, seed_data):
        event = AlchemyEvent(server_id=seed_data["server"].id, name="DailyTest", total_days=30)
        test_db.add(event)
        test_db.commit()
        activity = DailyCorActivity(
            day_index=1, status_code=1,
            character_id=seed_data["character"].id,
            event_id=event.id
        )
        test_db.add(activity)
        test_db.commit()
        assert activity.id is not None
        assert activity.day_index == 1


class TestTombolaModels:
    def test_tombola_event_tablename(self):
        assert TombolaEvent.__tablename__ == 'tombola_events'

    def test_tombola_activity_tablename(self):
        assert TombolaActivity.__tablename__ == 'tombola_activities'

    def test_tombola_item_counter_tablename(self):
        assert TombolaItemCounter.__tablename__ == 'tombola_item_counters'

    def test_create_tombola_event(self, test_db, seed_data):
        event = TombolaEvent(server_id=seed_data["server"].id, name="Tombola Test")
        test_db.add(event)
        test_db.commit()
        assert event.id is not None

    def test_create_item_counter(self, test_db, seed_data):
        event = TombolaEvent(server_id=seed_data["server"].id, name="Counter Test")
        test_db.add(event)
        test_db.commit()
        counter = TombolaItemCounter(event_id=event.id, item_name="Gema", count=5)
        test_db.add(counter)
        test_db.commit()
        assert counter.count == 5
        assert counter.item_name == "Gema"


class TestTimerRecordModel:
    def test_tablename(self):
        assert TimerRecord.__tablename__ == 'timer_records'

    def test_create_record(self, test_db):
        record = TimerRecord(name="Timer Test", elapsed_seconds=120)
        test_db.add(record)
        test_db.commit()
        assert record.id is not None
        assert record.elapsed_seconds == 120


class TestDailyCorRecordModel:
    def test_tablename(self):
        assert DailyCorRecord.__tablename__ == 'daily_cor_records'

    def test_create_record(self, test_db, seed_data):
        event = AlchemyEvent(server_id=seed_data["server"].id, name="CordTest", total_days=30)
        test_db.add(event)
        test_db.commit()
        record = DailyCorRecord(
            game_account_id=seed_data["game_account"].id,
            event_id=event.id,
            day_index=1,
            cords_count=3
        )
        test_db.add(record)
        test_db.commit()
        assert record.cords_count == 3


class TestAlchemyCounterModel:
    def test_tablename(self):
        assert AlchemyCounter.__tablename__ == 'alchemy_counters'

    def test_create_counter(self, test_db, seed_data):
        event = AlchemyEvent(server_id=seed_data["server"].id, name="AlcCounterTest", total_days=30)
        test_db.add(event)
        test_db.commit()
        counter = AlchemyCounter(event_id=event.id, alchemy_type="diamante", count=10)
        test_db.add(counter)
        test_db.commit()
        assert counter.alchemy_type == "diamante"
        assert counter.count == 10
