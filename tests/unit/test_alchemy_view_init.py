import pytest
from PyQt6.QtWidgets import QApplication, QWidget
from unittest.mock import MagicMock, patch

# Fixture for QApplication
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_alchemy_view_import(qapp):
    """
    Test that AlchemyView can be imported and instantiated without ModuleNotFoundError.
    This specifically tests for the regression where 'app.controllers' was missing.
    """
    try:
        from app.presentation.views.alchemy_view import AlchemyView
    except ImportError as e:
        pytest.fail(f"Failed to import AlchemyView: {e}")

    # Mock dependencies for instantiation if we wanted to go further
    # But import alone proves the fix for 'ModuleNotFoundError: No module named app.controllers'
    # because that error happened at module level or during method execution when importing locally.
    
    # Actually, the error was inside a method: on_import_requested
    # So we should test that method or check the top-level imports don't fail.
    # The traceback in step 0 showed it failed at line 846 inside on_import_requested:
    # `from app.controllers.import_controller import ImportController`
    
    # So we must inspect that specific import or define a test that exercises it.
    
    from app.presentation.views.alchemy_view import AlchemyView
    # Since the import is LOCAL to the method, simply importing the module won't trigger it.
    # We must check the file content or run the method.
    # Running the method requires a full view instance.
    
    # Let's try to verify the import path exists via inspection or simple instantiation + method call with mocks.
    pass

import sys
from unittest.mock import MagicMock, patch

def test_alchemy_view_import_logic(qapp):
    """
    Simulate the action that caused the crash to verify the fix.
    """
    # We must patch where the objects are looking up.
    # AlchemyService is imported at module level in alchemy_view.
    # AlchemyCountersWidget is imported inside __init__ from its module.
    # ImportService is imported inside on_import_requested from its module.
    
    # Create a mock widget that inherits from QWidget and has required methods
    class MockAlchemyCountersWidget(QWidget):
        def set_event(self, event_id):
            pass
        def update_cords_display(self):
            pass

    with patch('app.presentation.views.alchemy_view.AlchemyService') as MockService, \
         patch('app.presentation.views.widgets.alchemy_counters_widget.AlchemyCountersWidget') as MockWidgetClass, \
         patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=('dummy.xlsx', 'filter')), \
         patch('app.application.services.import_service.ImportService'), \
         patch('app.utils.excel_importer.parse_account_file', return_value=[]) as MockParse: # Added Mock
         
        # Configure Mock Service
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.name = "Test Event"
        mock_event.total_days = 30
        import datetime
        mock_event.created_at = datetime.date.today()
        
        service_instance = MockService.return_value
        service_instance.get_alchemy_events.return_value = [mock_event]
        service_instance.get_alchemy_dashboard_data.return_value = []
        # get_next_pending_day used in batch logic, maybe not called in init but good to satisfy
        service_instance.get_server_flags.return_value = {}

        # Make the mock class return our custom widget
        MockWidgetClass.return_value = MockAlchemyCountersWidget()
        
        from app.presentation.views.alchemy_view import AlchemyView
        
        # Instantiate view
        # This will call __init__, which imports AlchemyCountersWidget (now mocked)
        view = AlchemyView(server_id=1, server_name="TestServer")
        
        # Trigger the import method
        # This will import ImportService and parse_account_file
        try:
            view.on_import_requested()
        except ImportError as e:
            pytest.fail(f"ImportError during on_import_requested: {e}")
        except ModuleNotFoundError as e:
             pytest.fail(f"ModuleNotFoundError during on_import_requested: {e}")
            
        # Verify pars_account_file was used
        MockParse.assert_called_once()
