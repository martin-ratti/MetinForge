import pytest
import sys
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import Qt
from app.views.main_menu_view import MainMenuView
from app.views.server_selection_view import ServerSelectionView
from app.main import MainWindow

@pytest.fixture(scope="session")
def qapp():
    """Ensure QApplication exists."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

def test_app_launch(qtbot, qapp):
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

def test_navigation_to_server_selection(qtbot, qapp):
    """Test navigation from Main Menu to Server Selection."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Get Main Menu
    main_menu = window.centralWidget()
    assert isinstance(main_menu, MainMenuView)
    
    # Find the 'GESTIONAR SERVIDORES' button
    # Based on main_menu_view.py, it's created via create_main_button
    # We can iterate children or simply find by text if possible, but finding by type is safer usually.
    # The text is "GESTIONAR SERVIDORES"
    
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

