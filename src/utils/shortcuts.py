from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

class ShortcutManager:
    """
    Centralized keyboard shortcut manager for MetinForge.
    
    Usage:
        manager = ShortcutManager(self)
        manager.register('Ctrl+A', self.select_all)
        manager.register('1', lambda: self.mark_day(1))
    """
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.shortcuts = {}
    
    def register(self, key_sequence: str, callback):
        """
        Register a keyboard shortcut.
        
        Args:
            key_sequence: Key combination (e.g., 'Ctrl+A', '1', 'Shift+D')
            callback: Function to call when shortcut is triggered
        """
        shortcut = QShortcut(QKeySequence(key_sequence), self.parent)
        shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        shortcut.activated.connect(callback)
        self.shortcuts[key_sequence] = shortcut
    
    def unregister(self, key_sequence: str):
        """Remove a keyboard shortcut."""
        if key_sequence in self.shortcuts:
            self.shortcuts[key_sequence].deleteLater()
            del self.shortcuts[key_sequence]
    
    def clear_all(self):
        """Remove all registered shortcuts."""
        for shortcut in self.shortcuts.values():
            shortcut.deleteLater()
        self.shortcuts.clear()


def register_shortcuts(widget: QWidget, handlers: dict) -> ShortcutManager:
    """
    Convenience function to register multiple shortcuts at once.
    
    Args:
        widget: Parent QWidget
        handlers: Dict mapping key sequences to callbacks
                  Example: {'Ctrl+A': select_all_fn, '1': mark_day_1_fn}
    
    Returns:
        ShortcutManager instance for further management
    """
    manager = ShortcutManager(widget)
    for key_seq, callback in handlers.items():
        manager.register(key_seq, callback)
    return manager
