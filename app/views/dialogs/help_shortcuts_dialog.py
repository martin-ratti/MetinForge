from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
from PyQt6.QtCore import Qt

class HelpShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayuda: Atajos y Gestión Masiva")
        self.setMinimumWidth(500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; }
            QLabel { color: #eceff1; font-size: 14px; }
            .title { font-size: 18px; font-weight: bold; color: #d4af37; border-bottom: 2px solid #5d4d2b; padding-bottom: 10px; }
            .shortcut { color: #ffca28; font-weight: bold; font-family: 'Consolas', monospace; }
            .desc { color: #b0bec5; }
            QPushButton { background-color: #455a64; color: white; border-radius: 4px; padding: 8px 20px; font-weight: bold; }
            QPushButton:hover { background-color: #607d8b; }
        """)
        
        # Header
        title = QLabel("Guía de Productividad")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Grid for shortcuts
        grid = QGridLayout()
        grid.setSpacing(15)
        
        shortcuts = [
            ("Ctrl + A", "Seleccionar todas las cuentas visibles"),
            ("Ctrl + D", "Deseleccionar todas"),
            ("Shift + Click", "Seleccionar un rango de cuentas"),
            ("Ctrl + Click", "Seleccionar cuentas individuales"),
            ("1", "Marcar seleccionadas como HECHO ✅"),
            ("2", "Marcar seleccionadas como FALLIDO ❌"),
            ("3", "REINICIAR estado de seleccionadas ♻️"),
            ("Importar", "Carga masiva desde .xlsx o .csv\n(Formato: Email en A1, PJs abajo)")
        ]
        
        for ui_idx, (key, desc) in enumerate(shortcuts):
            k_lbl = QLabel(key)
            k_lbl.setProperty("class", "shortcut")
            d_lbl = QLabel(desc)
            d_lbl.setProperty("class", "desc")
            d_lbl.setWordWrap(True)
            
            grid.addWidget(k_lbl, ui_idx, 0)
            grid.addWidget(d_lbl, ui_idx, 1)
            
        layout.addLayout(grid)
        
        # Footer
        btn_close = QPushButton("Entendido")
        btn_close.clicked.connect(self.accept)
        
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(btn_close)
        layout.addLayout(footer)
