from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt

class SaveRecordDialog(QDialog):
    def __init__(self, time_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guardar Registro")
        self.setModal(True)
        self.setFixedSize(500, 220)
        
        # Window flags
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Time label
        lbl_time = QLabel(f"Tiempo: {time_str}")
        lbl_time.setWordWrap(True)
        lbl_time.setStyleSheet("""
            font-size: 20px;
            color: #d4af37;
            font-weight: bold;
            margin-bottom: 10px;
            padding: 5px;
        """)
        lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_time)
        
        # Name label
        lbl_name = QLabel("Nombre del registro:")
        lbl_name.setStyleSheet("""
            font-size: 14px;
            color: #e0e0e0;
            font-weight: bold;
        """)
        layout.addWidget(lbl_name)
        
        # Input
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Ej: Boss Run, Dungeon Clear...")
        self.input_name.setFixedHeight(40)
        self.input_name.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 2px solid #5d4d2b;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #d4af37;
            }
        """)
        layout.addWidget(self.input_name)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_ok = QPushButton("Guardar")
        btn_ok.setFixedHeight(35)
        btn_ok.clicked.connect(self.accept)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #2b1d0e;
                color: #d4af37;
                border: 2px solid #5d4d2b;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #3d2b1f;
                border: 2px solid #d4af37;
            }
            QPushButton:pressed {
                background-color: #d4af37;
                color: #000;
            }
        """)
        btn_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(35)
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #550000;
                color: #ffcccc;
                border: 2px solid #800000;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #800000;
                border: 2px solid #ff4444;
            }
        """)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        # Overall style
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                border: 3px solid #d4af37;
                border-radius: 10px;
            }
        """)
        
        # Set focus to input
        self.input_name.setFocus()
    
    def get_name(self):
        return self.input_name.text().strip()
