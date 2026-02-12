import pytest
from unittest.mock import MagicMock
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QApplication

from app.presentation.models.tombola_model import TombolaModel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def _make_store_data(email="test@store.com", accounts=None):
    """Helper: crea estructura de datos mock para TombolaModel."""
    if accounts is None:
        acc = MagicMock()
        acc.username = "TestUser"
        acc.characters = [MagicMock(name="Tombola1", id=1)]
        acc.characters[0].tombola_activities = []
        accounts = [acc]
    return {"store": MagicMock(email=email, id=1), "accounts": accounts}


class TestTombolaModelEmpty:
    def test_empty_model_no_rows(self, qapp):
        model = TombolaModel()
        assert model.rowCount(QModelIndex()) == 0

    def test_empty_model_columns(self, qapp):
        model = TombolaModel()
        assert model.columnCount(QModelIndex()) == 3


class TestTombolaModelWithData:
    def test_set_data_updates_rows(self, qapp):
        model = TombolaModel()
        data = [_make_store_data(), _make_store_data(email="store2@mail.com")]
        model.set_data(data, 1)
        assert model.rowCount(QModelIndex()) == 2

    def test_store_display_role(self, qapp):
        model = TombolaModel()
        data = [_make_store_data(email="tombola@mail.com")]
        model.set_data(data, 1)
        
        index = model.index(0, 0)
        assert index.isValid()
        display = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert "tombola@mail.com" in str(display)

    def test_store_type_role(self, qapp):
        model = TombolaModel()
        data = [_make_store_data()]
        model.set_data(data, 1)
        
        index = model.index(0, 0)
        type_val = model.data(index, TombolaModel.TypeRole)
        assert type_val == "store"

    def test_account_children(self, qapp):
        model = TombolaModel()
        acc = MagicMock()
        acc.username = "TestUser"
        acc.characters = [MagicMock(name="Char1", id=1)]
        acc.characters[0].tombola_activities = []
        data = [_make_store_data(accounts=[acc])]
        model.set_data(data, 1)
        
        store_index = model.index(0, 0)
        child_count = model.rowCount(store_index)
        assert child_count == 1

    def test_headers(self, qapp):
        model = TombolaModel()
        h0 = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        h1 = model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        h2 = model.headerData(2, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert h0 == "Cuenta"
        assert h1 == "Personaje"
        assert h2 == "Registro Diario"

    def test_set_data_resets_model(self, qapp):
        model = TombolaModel()
        data1 = [_make_store_data()]
        model.set_data(data1, 1)
        assert model.rowCount(QModelIndex()) == 1
        
        model.set_data([], 1)
        assert model.rowCount(QModelIndex()) == 0
