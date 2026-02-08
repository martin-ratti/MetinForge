from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from app.presentation.views.layouts.flow_layout import FlowLayout

class DayButton(QPushButton):
    # Señal que emite (dia, nuevo_estado) cuando cambia
    statusChanged = pyqtSignal(int, int)

    def __init__(self, day_index, status=0):
        super().__init__()
        self.day_index = day_index
        self.status = status  # 0: Pendiente, 1: Hecho, -1: Fallido
        self.setFixedSize(22, 22) # Botones ajustados (20 era muy chico, 30 muy grande)
        self.update_style()
        
        # Conectamos el click
        self.clicked.connect(self.toggle_status)

    def toggle_status(self):
        if not self.isEnabled():
             return

        original_status = self.status
        if self.status == 0: self.status = 1
        elif self.status == 1: self.status = -1
        else: self.status = 0
        
        self.update_style()
        self.statusChanged.emit(self.day_index, self.status)

    def update_style(self):
        font_style = "font-weight: bold; font-size: 12px;" # Aumentado de 11px a 12px
        
        if self.status == 1:
            self.setText("✓")
            # Metin2 Success - Gold
            self.setStyleSheet(f"background-color: #d4af37; color: #000; border: 1px solid #5d4d2b; border-radius: 2px; {font_style}") 
            self.setToolTip(f"Día {self.day_index}: Completado")
        elif self.status == -1:
            self.setText("✕")
            # Metin2 Fail - Dark Red
            self.setStyleSheet(f"background-color: #550000; color: #ffcccc; border: 1px solid #800000; border-radius: 2px; {font_style}")
            self.setToolTip(f"Día {self.day_index}: Fallido / No hecho")
        else:
            self.setText("")
            # Metin2 Pending - Dark Background with Gold Border
            self.setStyleSheet(f"background-color: #2b2b2b; border: 1px solid #5d4d2b; border-radius: 2px; {font_style}")
            self.setToolTip(f"Día {self.day_index}: Pendiente")

    def setOpacity(self, opacity):
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        op = QGraphicsOpacityEffect(self)
        op.setOpacity(opacity)
        self.setGraphicsEffect(op)

class DailyGridWidget(QWidget):
    # Re-emitimos la señal del botón: (día, nuevo_estado)
    statusChanged = pyqtSignal(int, int)

    def __init__(self, days_data=None, total_days=31):
        super().__init__()
        # Use Custom FlowLayout
        self.layout = FlowLayout(spacing=2) # Spacing minimo
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(self.layout)
        
        self.buttons = []
        
        for i in range(1, total_days + 1):
            initial_status = days_data.get(i, 0) if days_data else 0
            
            btn = DayButton(i, initial_status)
            btn.statusChanged.connect(self.handle_button_change)
            
            self.layout.addWidget(btn)
            self.buttons.append(btn)
        
        self.refresh_enable_states()

    def handle_button_change(self, day, status):
        # Re-emit signal
        self.statusChanged.emit(day, status)
        # Refresh states after change
        self.refresh_enable_states()
        
    def refresh_enable_states(self):
        previous_done = True 
        
        for btn in self.buttons:
            if previous_done:
                btn.setEnabled(True)
                btn.setOpacity(1.0)
            else:
                btn.setEnabled(False) 
            
            # Update previous_done for next iteration
            # Considered done if status != 0
            if btn.status == 0:
                previous_done = False
            else:
                previous_done = True
            
        # Policy: Horizontal Expanding (to wrap), Vertical Fixed/Minimum (to hug content)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

class DailyGridHeaderWidget(QWidget):
    def __init__(self, total_days=31):
        super().__init__()
        self.layout = FlowLayout(spacing=2)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        for i in range(1, total_days + 1):
            l = QLabel(str(i))
            l.setFixedSize(22, 22) # MATCH DayButton Size
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setStyleSheet("color: #a0a0a0; font-size: 11px; font-weight: bold;")
            
            self.layout.addWidget(l)

        # Policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
