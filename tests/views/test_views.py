import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
import datetime


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestFeatureSelectionView:
    """Tests para FeatureSelectionView."""

    def test_all_flags_enabled_shows_three_cards(self, qapp):
        from app.presentation.views.feature_selection_view import FeatureSelectionView
        flags = {"has_dailies": True, "has_fishing": True, "has_tombola": True}
        view = FeatureSelectionView(server_name="TestServer", flags=flags)
        
        from app.presentation.views.widgets.feature_card_button import FeatureCardButton
        cards = view.findChildren(FeatureCardButton)
        assert len(cards) == 3

    def test_no_fishing_shows_two_cards(self, qapp):
        from app.presentation.views.feature_selection_view import FeatureSelectionView
        flags = {"has_dailies": True, "has_fishing": False, "has_tombola": True}
        view = FeatureSelectionView(server_name="TestServer", flags=flags)
        
        from app.presentation.views.widgets.feature_card_button import FeatureCardButton
        cards = view.findChildren(FeatureCardButton)
        assert len(cards) == 2

    def test_no_flags_shows_three_cards_default(self, qapp):
        """Sin flags explícitos, defaults son True."""
        from app.presentation.views.feature_selection_view import FeatureSelectionView
        flags = {}
        view = FeatureSelectionView(server_name="TestServer", flags=flags)
        
        from app.presentation.views.widgets.feature_card_button import FeatureCardButton
        cards = view.findChildren(FeatureCardButton)
        assert len(cards) == 3

    def test_only_dailies_shows_one_card(self, qapp):
        from app.presentation.views.feature_selection_view import FeatureSelectionView
        flags = {"has_dailies": True, "has_fishing": False, "has_tombola": False}
        view = FeatureSelectionView(server_name="TestServer", flags=flags)
        
        from app.presentation.views.widgets.feature_card_button import FeatureCardButton
        cards = view.findChildren(FeatureCardButton)
        assert len(cards) == 1

    def test_feature_selected_signal(self, qapp, qtbot):
        from app.presentation.views.feature_selection_view import FeatureSelectionView
        flags = {"has_dailies": True, "has_fishing": True, "has_tombola": True}
        view = FeatureSelectionView(server_name="TestServer", flags=flags)
        
        with qtbot.waitSignal(view.featureSelected, timeout=1000) as blocker:
            view.featureSelected.emit("dailies")
        assert blocker.args == ["dailies"]

    def test_back_requested_signal(self, qapp, qtbot):
        from app.presentation.views.feature_selection_view import FeatureSelectionView
        flags = {"has_dailies": True, "has_fishing": True, "has_tombola": True}
        view = FeatureSelectionView(server_name="TestServer", flags=flags)
        
        with qtbot.waitSignal(view.backRequested, timeout=1000):
            view.backRequested.emit()


class TestServerSelectionView:
    """Tests para ServerSelectionView."""

    def test_init_creates_view(self, qapp):
        with patch('app.presentation.views.server_selection_view.AlchemyService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_alchemy_events.return_value = []
            
            from app.presentation.views.server_selection_view import ServerSelectionView
            view = ServerSelectionView()
            assert view is not None

    def test_signals_exist(self, qapp):
        with patch('app.presentation.views.server_selection_view.AlchemyService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_alchemy_events.return_value = []
            
            from app.presentation.views.server_selection_view import ServerSelectionView
            view = ServerSelectionView()
            assert hasattr(view, 'serverSelected')
            assert hasattr(view, 'backRequested')


class TestAlchemyViewInit:
    """Tests de import y init para AlchemyView (fusionados desde test_alchemy_view_init.py)."""

    def test_alchemy_view_import(self, qapp):
        """Verifica que AlchemyView se puede importar sin ModuleNotFoundError."""
        try:
            from app.presentation.views.alchemy_view import AlchemyView
        except ImportError as e:
            pytest.fail(f"Failed to import AlchemyView: {e}")

    def test_alchemy_view_import_logic(self, qapp):
        """Simula la accion de importacion para verificar que no hay errores de modulo."""
        class MockAlchemyCountersWidget(QWidget):
            def set_event(self, event_id):
                pass
            def update_cords_display(self):
                pass

        with patch('app.presentation.views.alchemy_view.AlchemyService') as MockService, \
             patch('app.presentation.views.widgets.alchemy_counters_widget.AlchemyCountersWidget') as MockWidgetClass, \
             patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=('dummy.xlsx', 'filter')), \
             patch('app.utils.excel_importer.parse_account_file', return_value=[]) as MockParse, \
             patch('app.presentation.views.alchemy_view.QMessageBox'):
             
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

