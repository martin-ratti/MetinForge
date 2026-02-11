import pytest
from PyQt6.QtCore import Qt
from app.presentation.models.alchemy_model import AlchemyModel
from unittest.mock import MagicMock

@pytest.fixture
def mock_store_data():
    # Mock Store
    store = MagicMock()
    store.email = "test@store.com"
    store.id = 1
    
    # Mock Character
    char = MagicMock()
    char.name = "TestChar"
    char.id = 101
    
    # Mock Account
    account = MagicMock()
    account.username = "TestAccount"
    account.characters = [char]
    account.id = 50
    account.current_event_activity = {1: 1, 2: -1} # Day 1: Success, Day 2: Fail
    
    return [{'store': store, 'accounts': [account]}]

def test_alchemy_model_structure(mock_store_data):
    model = AlchemyModel(data=mock_store_data)
    
    # Root level (Stores)
    assert model.rowCount() == 1
    
    # Store Index
    store_index = model.index(0, 0)
    assert store_index.isValid()
    assert model.data(store_index, Qt.ItemDataRole.DisplayRole) == "📧 test@store.com"
    assert model.data(store_index, AlchemyModel.TypeRole) == "store"
    
    # Account level
    assert model.rowCount(store_index) == 1
    account_index = model.index(0, 0, store_index)
    assert account_index.isValid()
    assert model.data(account_index, AlchemyModel.TypeRole) == "account"
    assert model.data(account_index, Qt.ItemDataRole.DisplayRole) == "TestAccount"
    
    # Parent check
    assert model.parent(account_index) == store_index
    assert model.parent(store_index).isValid() == False

def test_alchemy_model_grid_data(mock_store_data):
    model = AlchemyModel(data=mock_store_data)
    store_index = model.index(0, 0)
    account_index = model.index(0, 3, store_index) # Grid Column is 3
    
    grid_data = model.data(account_index, AlchemyModel.GridDataRole)
    assert grid_data == {1: 1, 2: -1}

def test_alchemy_model_columns(mock_store_data):
    model = AlchemyModel(data=mock_store_data)
    assert model.columnCount() == 5
    
    # Check headers
    assert model.headerData(3, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == "Registro Diario"

def test_alchemy_model_cords_data(mock_store_data):
    model = AlchemyModel(data=mock_store_data)
    # Mock Cords Summary: {account_id: {day: count}}
    cords_summary = {50: {1: 5, 2: 10}} 
    model.set_data(mock_store_data, event_id=1, cords_summary=cords_summary)
    
    store_index = model.index(0, 0)
    account_index = model.index(0, 0, store_index)
    
    # Default current day is 1
    # Check column 4 (Cords)
    cords_index = model.index(0, 4, store_index)
    assert model.data(cords_index, AlchemyModel.CordsRole) == 5
    
    # Change day
    model._current_day = 2
    assert model.data(cords_index, AlchemyModel.CordsRole) == 10
    
    # Day without data
    model._current_day = 3
    assert model.data(cords_index, AlchemyModel.CordsRole) == 0
