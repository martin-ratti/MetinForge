import pytest
from app.utils.config import Config
from app.utils.shortcuts import ShortcutManager
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QKeySequence

def test_config_db_url(monkeypatch):
    monkeypatch.setattr(Config, 'DB_USER', 'testuser')
    monkeypatch.setattr(Config, 'DB_PASSWORD', 'testpass')
    monkeypatch.setattr(Config, 'DB_HOST', '127.0.0.1')
    monkeypatch.setattr(Config, 'DB_PORT', '3307')
    monkeypatch.setattr(Config, 'DB_NAME', 'testdb')
    
    expected_url = "mysql+pymysql://testuser:testpass@127.0.0.1:3307/testdb"
    assert Config.get_db_url() == expected_url

def test_shortcut_manager(qtbot):
    widget = QWidget()
    manager = ShortcutManager(widget)
    
    called = False
    def callback():
        nonlocal called
        called = True
        
    manager.register('Ctrl+T', callback)
    assert 'Ctrl+T' in manager.shortcuts
    
    # Clean up
    manager.unregister('Ctrl+T')
    assert 'Ctrl+T' not in manager.shortcuts
    
    manager.clear_all()
