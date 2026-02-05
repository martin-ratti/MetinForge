import pytest
import sys
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import Qt
from app.views.main_menu_view import MainMenuView
from app.views.server_selection_view import ServerSelectionView
from app.main import MainWindow



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

    with patch('app.views.server_selection_view.AlchemyController') as MockController:
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

