from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QSpinBox, QDialogButtonBox, QFormLayout)
from PyQt6.QtCore import Qt

class EventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Jornada / Evento")
        self.setFixedWidth(300)
        self.setStyleSheet("""
            QDialog { background-color: #263238; color: #eceff1; }
            QLabel { color: #b0bec5; font-size: 13px; font-weight: bold; }
            QLineEdit, QSpinBox { 
                background-color: #37474f; 
                color: white; 
                border: 1px solid #546e7a; 
                padding: 5px; 
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Ej: Evento Marzo")
        
        self.spin_days = QSpinBox()
        self.spin_days.setRange(1, 365)
        self.spin_days.setValue(30)
        
        form_layout.addRow("Nombre:", self.txt_name)
        form_layout.addRow("Duración (Días):", self.spin_days)
        
        layout.addLayout(form_layout)
        
        layout.addSpacing(10)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.buttons.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; border-radius: 4px; padding: 6px 15px; } QPushButton:hover { background-color: #388e3c; }")
        
        layout.addWidget(self.buttons)
        
    def get_data(self):
        return self.txt_name.text().strip(), self.spin_days.value()
