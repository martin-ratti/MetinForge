from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QShortcut, QKeySequence

class ShortcutManager:
    """Gestor de atajos de teclado para la aplicacion."""
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.shortcuts = {}

    def register(self, key_sequence: str, callback):
        shortcut = QShortcut(QKeySequence(key_sequence), self.parent)
        shortcut.activated.connect(callback)
        self.shortcuts[key_sequence] = shortcut
        return shortcut

    def unregister(self, key_sequence: str):
        if key_sequence in self.shortcuts:
            self.shortcuts[key_sequence].setEnabled(False)
            del self.shortcuts[key_sequence]

    def clear_all(self):
        for sc in self.shortcuts.values():
            sc.setEnabled(False)
        self.shortcuts.clear()


def register_shortcuts(widget: QWidget, handlers: dict) -> ShortcutManager:
    """Registra multiples atajos de teclado en un widget."""
    manager = ShortcutManager(widget)
    for key_seq, callback in handlers.items():
        manager.register(key_seq, callback)
    return manager
