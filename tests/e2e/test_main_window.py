import pytest
import sys
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import Qt
from app.presentation.views.main_menu_view import MainMenuView
from app.presentation.views.server_selection_view import ServerSelectionView
from main import MainWindow



def test_app_launch(qtbot):
    """Test that the main window launches and shows the main menu."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Wait for window to be exposed
    qtbot.waitForWindowShown(window)
    
    # Check if central widget is MainMenuView
    assert isinstance(window.centralWidget(), MainMenuView)
    
    # Check title
    assert window.windowTitle() == "MetinForge Manager v1.0"

def test_navigation_to_server_selection(qtbot):
    """Test navigation from Main Menu to Server Selection."""
    # Patch the AlchemyController used in ServerSelectionView
    from unittest.mock import MagicMock, patch
    
    # Mock data
    mock_server = MagicMock()
    mock_server.id = 1
    mock_server.name = "TestServer"
    mock_server.has_dailies = True
    mock_server.has_fishing = True
    mock_server.has_tombola = True

    with patch('app.presentation.views.server_selection_view.AlchemyService') as MockController:
        instance = MockController.return_value
        instance.get_servers.return_value = [mock_server]
        
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        
        # Get Main Menu
        main_menu = window.centralWidget()
        assert isinstance(main_menu, MainMenuView)
        
        # Find the 'GESTIONAR SERVIDORES' button
        buttons = main_menu.findChildren(QPushButton)
        server_btn = None
        for btn in buttons:
            if btn.text() == "GESTIONAR SERVIDORES":
                server_btn = btn
                break
                
        assert server_btn is not None, "Server button not found"
        
        # Click the button
        qtbot.mouseClick(server_btn, Qt.MouseButton.LeftButton)
        
        # Check if central widget changed to ServerSelectionView
        assert isinstance(window.centralWidget(), ServerSelectionView)


def test_back_from_server_selection(qtbot):
    """Test navigation back from Server Selection to Main Menu."""
    from unittest.mock import MagicMock, patch
    
    with patch('app.presentation.views.server_selection_view.AlchemyService') as MockController:
        instance = MockController.return_value
        instance.get_servers.return_value = []
        
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        
        main_menu = window.centralWidget()
        buttons = main_menu.findChildren(QPushButton)
        server_btn = None
        for btn in buttons:
            if btn.text() == "GESTIONAR SERVIDORES":
                server_btn = btn
                break
        
        assert server_btn is not None
        qtbot.mouseClick(server_btn, Qt.MouseButton.LeftButton)
        assert isinstance(window.centralWidget(), ServerSelectionView)
        
        # Find back button
        server_view = window.centralWidget()
        back_buttons = server_view.findChildren(QPushButton)
        back_btn = None
        for btn in back_buttons:
            if "Volver" in btn.text() or "volver" in btn.text().lower():
                back_btn = btn
                break
        
        if back_btn:
            qtbot.mouseClick(back_btn, Qt.MouseButton.LeftButton)
            assert isinstance(window.centralWidget(), MainMenuView)


def test_feature_selection_navigation(qtbot):
    """Test that ServerSelectionView has working signals after navigation."""
    from unittest.mock import MagicMock, patch
    
    mock_server = MagicMock()
    mock_server.id = 1
    mock_server.name = "TestServer"
    mock_server.has_dailies = True
    mock_server.has_fishing = True
    mock_server.has_tombola = True

    with patch('app.presentation.views.server_selection_view.AlchemyService') as MockController:
        instance = MockController.return_value
        instance.get_servers.return_value = [mock_server]
        
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        
        # Navigate to server selection
        main_menu = window.centralWidget()
        buttons = main_menu.findChildren(QPushButton)
        server_btn = None
        for btn in buttons:
            if btn.text() == "GESTIONAR SERVIDORES":
                server_btn = btn
                break
        
        assert server_btn is not None
        qtbot.mouseClick(server_btn, Qt.MouseButton.LeftButton)
        
        # Verify we're in ServerSelectionView and it has the right signals
        server_view = window.centralWidget()
        assert isinstance(server_view, ServerSelectionView)
        assert hasattr(server_view, 'serverSelected')
        assert hasattr(server_view, 'backRequested')


