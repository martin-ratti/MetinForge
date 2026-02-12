import pytest
from PyQt6.QtWidgets import QApplication, QWidget
from unittest.mock import MagicMock, patch
import sys
import datetime

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_alchemy_view_import(qapp):
    """Verifica que AlchemyView se puede importar sin ModuleNotFoundError."""
    try:
        from app.presentation.views.alchemy_view import AlchemyView
    except ImportError as e:
        pytest.fail(f"Failed to import AlchemyView: {e}")

def test_alchemy_view_import_logic(qapp):
    """Simula la accion de importacion para verificar que no hay errores de modulo."""
    class MockAlchemyCountersWidget(QWidget):
        def set_event(self, event_id):
            pass
        def update_cords_display(self):
            pass

    with patch('app.presentation.views.alchemy_view.AlchemyService') as MockService, \
         patch('app.presentation.views.widgets.alchemy_counters_widget.AlchemyCountersWidget') as MockWidgetClass, \
         patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=('dummy.xlsx', 'filter')), \
         patch('app.utils.excel_importer.parse_account_file', return_value=[]) as MockParse:
         
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.name = "Test Event"
        mock_event.total_days = 30
        mock_event.created_at = datetime.date.today()
        
        service_instance = MockService.return_value
        service_instance.get_alchemy_events.return_value = [mock_event]
        service_instance.get_alchemy_dashboard_data.return_value = []
        service_instance.get_server_flags.return_value = {}

        MockWidgetClass.return_value = MockAlchemyCountersWidget()
        
        from app.presentation.views.alchemy_view import AlchemyView
        
        view = AlchemyView(server_id=1, server_name="TestServer")
        
        try:
            view.on_import_requested()
        except ImportError as e:
            pytest.fail(f"ImportError during on_import_requested: {e}")
        except ModuleNotFoundError as e:
             pytest.fail(f"ModuleNotFoundError during on_import_requested: {e}")
            
        MockParse.assert_called_once()
