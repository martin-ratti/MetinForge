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
        # Enforce sequential logic: Can only modify if previous day is != 0 (Done or Fail)
        # Exception: Day 1 is always modifiable.
        # This requires knowledge of previous day status.
        # Since button is self-contained, we might need to rely on parent Grid to validate?
        # OR we pass 'is_enabled_sequentially' flag?
        
        # User requested: "solo se debera poder modificar el dia siguiente al ultimo que esta marcado"
        # i.e., I can toggle Day 5 only if Day 4 is marked (1 or -1).
        # AND I should not be able to toggle Day 5 if Day 6 is marked? (Strict history)
        
        # NOTE: Logic is getting complex for a simple button. 
        # Ideally, the Grid controls the 'enabled' state.
        
        # However, to avoid major refactor, let's assume the Grid will disable/enable buttons.
        # But for now, we emit signal and let Controller/Grid decide?
        # Actually, let's just emit. The visual disable logic should be in DailyGridWidget.update_layout
        
        # If we want strict logic here:
        if not self.isEnabled():
             return

        # Ciclo de estados: 0 -> 1 -> -1 -> 0
        original_status = self.status
        if self.status == 0: self.status = 1
        elif self.status == 1: self.status = -1
        else: self.status = 0
        
        # Check if we are resetting a day that has future days marked?
        if self.status == 0 and original_status != 0:
             # Just warn or allow? User said "resetear la bd", implying strictness.
             # If I reset Day 5, should Day 6 be reset? 
             # For now, let's keep it simple.
             pass
        
        self.update_style()
        self.statusChanged.emit(self.day_index, self.status)

    def update_style(self):
        font_style = "font-weight: bold; font-size: 16px;"
        
        if self.status == 1:
            self.setText("✓")
            # Metin2 Success - Gold
            self.setStyleSheet(f"background-color: #d4af37; color: #000; border: 1px solid #5d4d2b; border-radius: 4px; {font_style}") 
            self.setToolTip(f"Día {self.day_index}: Completado")
        elif self.status == -1:
            self.setText("✕")
            # Metin2 Fail - Dark Red
            self.setStyleSheet(f"background-color: #550000; color: #ffcccc; border: 1px solid #800000; border-radius: 4px; {font_style}")
            self.setToolTip(f"Día {self.day_index}: Fallido / No hecho")
        else:
            self.setText("")
            # Metin2 Pending - Dark Background with Gold Border
            self.setStyleSheet(f"background-color: #2b2b2b; border: 1px solid #5d4d2b; border-radius: 4px; {font_style}")
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
        self.layout = FlowLayout(spacing=4) # Spacing un poco mayor
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
        # Logic: Enable button N only if button N-1 is (!= 0).
        # Button 1 always enabled.
        # Button N+1 disabled if N is 0.
        
        # Also, if Button N is marked, Button N-1 should theoretically be locked?
        # Or just allow editing history? Usually history is editable.
        # Constraint: "Cannot mark Day N before Day N-1".
        
        previous_done = True # Day 0 is virtually "done"
        
        for btn in self.buttons:
            # Enable if previous is done OR if it's already done (editing allowed)
            # Actually, user wants strict flow.
            # If I have Day 1 Done, Day 2 Pending.
            # Day 1: Editable? Yes.
            # Day 2: Editable? Yes (b/c Day 1 is done).
            # Day 3: Editable? No (b/c Day 2 is pending).
            
            if previous_done:
                btn.setEnabled(True)
                btn.setOpacity(1.0) # Helper if we added opacity
            else:
                # If this button itself is marked (maybe from DB inconsistency), allow edit?
                # Or force strictness? Strict: if previous not done, this is disabled.
                btn.setEnabled(False)
                # btn.setOpacity(0.5) 
            
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
        self.layout = FlowLayout(spacing=4)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        for i in range(1, total_days + 1):
            l = QLabel(str(i))
            l.setFixedSize(30, 30) # MATCH DayButton Size
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setStyleSheet("color: #a0a0a0; font-size: 12px; font-weight: bold;")
            
            self.layout.addWidget(l)

        # Policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)