from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QSpinBox, QScrollArea,
                             QFrame, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal

class NoScrollSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class TombolaDashboardWidget(QWidget):
    """
    Panel lateral para la Tómbola.
    Muestra contadores de Talismanes y Premios del día.
    """
    
    def __init__(self, controller, event_id=None):
        super().__init__()
        self.controller = controller
        self.event_id = event_id
        
        # Data caches
        self.counters = {}
        self.spinboxes = {}
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)
        self.setLayout(layout)
        
        # Title
        lbl_title = QLabel("RESUMEN TÓMBOLA")
        lbl_title.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 14px; border-bottom: 2px solid #5d4d2b; padding-bottom: 5px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        # Scroll Area for Counters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(15)
        content.setLayout(self.content_layout)
        scroll.setWidget(content)
        
        # === SECCION PREMIOS DEL DÍA ===
        day_prize_section = QFrame()
        day_prize_section.setStyleSheet("""
            QFrame {
                background-color: #2d2d1b;
                border: 2px solid #d4af37;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        day_prize_layout = QVBoxLayout()
        day_prize_layout.setContentsMargins(10, 8, 10, 8)
        day_prize_layout.setSpacing(5)
        day_prize_section.setLayout(day_prize_layout)
        
        day_prize_title = QLabel("🏆 PREMIOS DEL DÍA")
        day_prize_title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #d4af37;
            border: none;
        """)
        day_prize_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        day_prize_layout.addWidget(day_prize_title)
        
        # Controls for Day Prize (Counter)
        dp_controls = QHBoxLayout()
        dp_controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dp_controls.setSpacing(10)
        
        btn_dp_minus = QPushButton("-")
        btn_dp_minus.setFixedSize(30, 30)
        btn_dp_minus.setStyleSheet("background-color: #550000; color: white; border: 1px solid #800000; border-radius: 4px; font-weight: bold; font-size: 14px;")
        
        self.spin_day_prize = NoScrollSpinBox()
        self.spin_day_prize.setRange(0, 9999)
        self.spin_day_prize.setFixedSize(80, 30)
        self.spin_day_prize.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_day_prize.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_day_prize.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a1a;
                color: #ffd700;
                border: 1px solid #d4af37;
                border-radius: 3px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        btn_dp_plus = QPushButton("+")
        btn_dp_plus.setFixedSize(30, 30)
        btn_dp_plus.setStyleSheet("background-color: #1b5e20; color: white; border: 1px solid #2e7d32; border-radius: 4px; font-weight: bold; font-size: 14px;")

        # Connect Logic
        btn_dp_minus.clicked.connect(lambda: self.spin_day_prize.setValue(self.spin_day_prize.value() - 1))
        btn_dp_plus.clicked.connect(lambda: self.spin_day_prize.setValue(self.spin_day_prize.value() + 1))
        self.spin_day_prize.valueChanged.connect(lambda val: self.on_counter_changed("Premios del día", val))
        
        # Add to local map for persistence
        self.spinboxes["Premios del día"] = self.spin_day_prize
        
        dp_controls.addWidget(btn_dp_minus)
        dp_controls.addWidget(self.spin_day_prize)
        dp_controls.addWidget(btn_dp_plus)
        
        day_prize_layout.addLayout(dp_controls)
        self.content_layout.addWidget(day_prize_section)
        
        # 1. Talismanes
        self.group_talismans = self.create_counter_group(
            "TALISMANES", 
            ["Viento", "Tierra", "Hielo", "Fuego", "Oscuridad", "Rayo"],
            color="#4fc3f7" # Light Blue
        )
        self.content_layout.addWidget(self.group_talismans)
        
        # 2. Premios
        self.group_prizes = self.create_counter_group(
            "PREMIOS", 
            ["Dioxido", "Adularia", "Jadita noche", "Refinados", 
             "Caja carta monstruo plata", "Baúl habilidad", 
             "Cofre manual mascota", "Alubia Verde", 
             "Hierba dorada", "Ágata"],
            color="#ffb74d" # Orange
        )
        self.content_layout.addWidget(self.group_prizes)
        
        self.content_layout.addStretch()
        layout.addWidget(scroll)
        
        self.load_data()

    def create_counter_group(self, title, items, color="#e0e0e0"):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #5d4d2b;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: {color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        grid = QGridLayout()
        grid.setSpacing(5)
        
        for i, item_name in enumerate(items):
            lbl = QLabel(item_name)
            lbl.setStyleSheet("color: #b0bec5; font-size: 11px;")
            
            spin = NoScrollSpinBox()
            spin.setRange(0, 9999)
            spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons) # Cleaner look
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setStyleSheet("""
                QSpinBox {
                    background-color: #263238;
                    color: white;
                    border: 1px solid #37474f;
                    border-radius: 3px;
                    padding: 2px;
                    font-weight: bold;
                }
                QSpinBox:focus {
                    border: 1px solid #d4af37;
                }
            """)
            # Fix lambda capture
            spin.valueChanged.connect(lambda val, k=item_name: self.on_counter_changed(k, val))
            
            self.spinboxes[item_name] = spin
            
            row = i
            grid.addWidget(lbl, row, 0)
            grid.addWidget(spin, row, 1)
            
        group.setLayout(grid)
        return group

    def load_data(self):
        if not self.event_id:
            self.setEnabled(False)
            # Reset values
            for spin in self.spinboxes.values():
                spin.blockSignals(True)
                spin.setValue(0)
                spin.blockSignals(False)
            return
            
        self.setEnabled(True)
        self.counters = self.controller.get_tombola_item_counters(self.event_id)
        
        for name, spin in self.spinboxes.items():
            if name in self.counters:
                spin.blockSignals(True)
                spin.setValue(self.counters[name])
                spin.blockSignals(False)
            else:
                spin.blockSignals(True)
                spin.setValue(0)
                spin.blockSignals(False)

    def on_counter_changed(self, item_name, value):
        if not self.event_id: return
        self.controller.update_tombola_item_count(self.event_id, item_name, value)
        
    def set_event_id(self, event_id):
        self.event_id = event_id
        self.load_data()
