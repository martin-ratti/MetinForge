import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


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
