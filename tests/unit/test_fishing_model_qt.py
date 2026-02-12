import pytest
from unittest.mock import MagicMock
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QApplication

from app.presentation.models.fishing_model import FishingModel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def _make_store_data(email="test@store.com", accounts=None):
    """Helper: crea estructura de datos mock para FishingModel."""
    if accounts is None:
        acc = MagicMock()
        acc.username = "TestUser"
        acc.characters = [MagicMock(name="Fisher1", id=1)]
        acc.characters[0].fishing_activities = []
        accounts = [acc]
    return {"store": MagicMock(email=email, id=1), "accounts": accounts}


class TestFishingModelEmpty:
    def test_empty_model_no_rows(self, qapp):
        model = FishingModel()
        assert model.rowCount(QModelIndex()) == 0

    def test_empty_model_columns(self, qapp):
        model = FishingModel()
        assert model.columnCount(QModelIndex()) == 3


class TestFishingModelWithData:
    def test_set_data_updates_rows(self, qapp):
        model = FishingModel()
        data = [_make_store_data(), _make_store_data(email="store2@mail.com")]
        model.set_data(data, 2026)
        assert model.rowCount(QModelIndex()) == 2

    def test_store_display_role(self, qapp):
        model = FishingModel()
        data = [_make_store_data(email="fisher@mail.com")]
        model.set_data(data, 2026)
        
        index = model.index(0, 0)
        assert index.isValid()
        display = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert "fisher@mail.com" in str(display)

    def test_store_type_role(self, qapp):
        model = FishingModel()
        data = [_make_store_data()]
        model.set_data(data, 2026)
        
        index = model.index(0, 0)
        type_val = model.data(index, FishingModel.TypeRole)
        assert type_val == "store"

    def test_account_children(self, qapp):
        model = FishingModel()
        acc = MagicMock()
        acc.username = "TestUser"
        acc.characters = [MagicMock(name="Fisher1", id=1)]
        acc.characters[0].fishing_activities = []
        data = [_make_store_data(accounts=[acc])]
        model.set_data(data, 2026)
        
        store_index = model.index(0, 0)
        child_count = model.rowCount(store_index)
        assert child_count == 1

    def test_headers(self, qapp):
        model = FishingModel()
        h0 = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        h1 = model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        h2 = model.headerData(2, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert h0 == "Cuenta"
        assert h1 == "Pescador"
        assert h2 == "Registro Anual"

    def test_set_data_resets_model(self, qapp):
        model = FishingModel()
        data1 = [_make_store_data()]
        model.set_data(data1, 2026)
        assert model.rowCount(QModelIndex()) == 1
        
        model.set_data([], 2026)
        assert model.rowCount(QModelIndex()) == 0
