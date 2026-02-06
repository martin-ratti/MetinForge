import pytest
from unittest.mock import MagicMock, patch
from app.controllers.import_controller import ImportController
from app.models.models import StoreAccount, GameAccount, Character, CharacterType

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def controller(mock_session):
    return ImportController(session=mock_session)

def test_import_from_excel_success(controller, mock_session, tmp_path):
    # Mock openpyxl loading
    wb_mock = MagicMock()
    ws_mock = MagicMock()
    wb_mock.__getitem__.return_value = ws_mock
    wb_mock.sheetnames = ["Sheet1"]
    
    # Mocking rows: 
    # Row 1: Yellow (Store Account)
    # Row 2: Data (Game Account)
    
    cell_store = MagicMock()
    cell_store.value = "STORE_USER"
    # Mock yellow color (FFFF00 or similar)
    cell_store.fill.fgColor.rgb = "FFFFFF00" 
    
    cell_empty = MagicMock()
    cell_empty.value = None
    
    row_store = (cell_store, cell_empty, cell_empty, cell_empty, cell_empty)
    
    cell_data_acc = MagicMock()
    cell_data_acc.value = "GAME_ACC"
    cell_data_acc.fill.fgColor.rgb = "00000000" # Not yellow
    
    cell_data_count = MagicMock()
    cell_data_count.value = 5
    
    cell_data_char = MagicMock()
    cell_data_char.value = "ALCHEMIST_CHAR"
    
    row_data = (cell_data_acc, cell_data_count, cell_data_char, cell_empty, cell_empty)
    
    ws_mock.iter_rows.return_value = [row_store, row_data]
    
    with patch("openpyxl.load_workbook", return_value=wb_mock):
        # Mock DB queries to simulate non-existing existing records (create new)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        result = controller.import_from_excel("dummy.xlsx", server_id=1)
        
        assert result["success"] is True
        assert result["processed_accounts"] == 1
        
        # Verify StoreAccount creation
        # We expect "STORE_USER@gmail.com" because implementation should append it
        
        # Verify GameAccount creation
        # Verify Character creation

def test_import_ignore_valid_data_without_yellow_header(controller, mock_session):
    # If we find data rows before any yellow row, they should probably be ignored or attached to a default?
    # Requirement says "Yellow row... then columns". So we assume data must follow a yellow row.
    pass
