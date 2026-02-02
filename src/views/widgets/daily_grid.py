from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QColor

class DayButton(QPushButton):
    # Señal que emite (dia, nuevo_estado) cuando cambia
    statusChanged = pyqtSignal(int, int)

    def __init__(self, day_index, status=0):
        super().__init__()
        self.day_index = day_index
        self.status = status  # 0: Pendiente, 1: Hecho, -1: Fallido
        self.setFixedSize(20, 20) # Botones compactos
        self.update_style()
        
        # Conectamos el click
        self.clicked.connect(self.toggle_status)

    def toggle_status(self):
        # Ciclo de estados: 0 -> 1 -> -1 -> 0
        if self.status == 0: self.status = 1
        elif self.status == 1: self.status = -1
        else: self.status = 0
        
        self.update_style()
        self.statusChanged.emit(self.day_index, self.status)

    def update_style(self):
        font_style = "font-weight: bold; font-size: 14px;"
        
        if self.status == 1:
            self.setText("✓")
            self.setStyleSheet(f"background-color: #2ecc71; color: white; border: none; border-radius: 2px; {font_style}") # Verde
            self.setToolTip(f"Día {self.day_index}: Completado")
        elif self.status == -1:
            self.setText("✕")
            self.setStyleSheet(f"background-color: #e74c3c; color: white; border: none; border-radius: 2px; {font_style}") # Rojo
            self.setToolTip(f"Día {self.day_index}: Fallido / No hecho")
        else:
            self.setText("")
            self.setStyleSheet(f"background-color: #34495e; border: 1px solid #5d6d7e; border-radius: 2px; {font_style}") # Gris
            self.setToolTip(f"Día {self.day_index}: Pendiente")

class DailyGridWidget(QWidget):
    # Re-emitimos la señal del botón: (día, nuevo_estado)
    statusChanged = pyqtSignal(int, int)

    def __init__(self, days_data=None):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)
        
        self.buttons = []
        
        # Crear 31 botones (días del mes)
        for i in range(1, 32):
            # Obtener estado inicial si existe
            initial_status = days_data.get(i, 0) if days_data else 0
            
            btn = DayButton(i, initial_status)
            
            # Conectar la señal del botón a la señal del widget
            btn.statusChanged.connect(self.statusChanged.emit)

            self.layout.addWidget(btn)
            self.buttons.append(btn)