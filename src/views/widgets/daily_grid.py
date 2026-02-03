from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from src.views.layouts.flow_layout import FlowLayout

class DayButton(QPushButton):
    # Señal que emite (dia, nuevo_estado) cuando cambia
    statusChanged = pyqtSignal(int, int)

    def __init__(self, day_index, status=0):
        super().__init__()
        self.day_index = day_index
        self.status = status  # 0: Pendiente, 1: Hecho, -1: Fallido
        self.setFixedSize(30, 30) # Botones MAS GRANDES
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
        font_style = "font-weight: bold; font-size: 16px;" # Letra mas grande
        
        if self.status == 1:
            self.setText("✓")
            self.setStyleSheet(f"background-color: #2ecc71; color: white; border: none; border-radius: 4px; {font_style}") 
            self.setToolTip(f"Día {self.day_index}: Completado")
        elif self.status == -1:
            self.setText("✕")
            self.setStyleSheet(f"background-color: #e74c3c; color: white; border: none; border-radius: 4px; {font_style}")
            self.setToolTip(f"Día {self.day_index}: Fallido / No hecho")
        else:
            self.setText("")
            self.setStyleSheet(f"background-color: #3f51b5; border: 1px solid #5c6bc0; border-radius: 4px; {font_style}") # Azul Metin
            self.setToolTip(f"Día {self.day_index}: Pendiente")

class DailyGridWidget(QWidget):
    # Re-emitimos la señal del botón: (día, nuevo_estado)
    statusChanged = pyqtSignal(int, int)

    def __init__(self, days_data=None, total_days=31):
        super().__init__()
        # Use Custom FlowLayout
        self.layout = FlowLayout(spacing=4) # Spacing un poco mayor
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(self.layout)
        
        self.buttons = []
        
        for i in range(1, total_days + 1):
            initial_status = days_data.get(i, 0) if days_data else 0
            
            btn = DayButton(i, initial_status)
            btn.statusChanged.connect(self.statusChanged.emit)
            
            self.layout.addWidget(btn)
            self.buttons.append(btn)
            
        # Policy: Horizontal Expanding (to wrap), Vertical Fixed/Minimum (to hug content)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

class DailyGridHeaderWidget(QWidget):
    def __init__(self, total_days=31):
        super().__init__()
        self.layout = FlowLayout(spacing=4)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        for i in range(1, total_days + 1):
            l = QLabel(str(i))
            l.setFixedSize(30, 30) # MATCH DayButton Size
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setStyleSheet("color: #cfd8dc; font-size: 12px; font-weight: bold;") # Texto mas visible
            
            self.layout.addWidget(l)

        # Policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)