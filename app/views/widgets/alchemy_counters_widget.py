from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QGridLayout, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal


class AlchemyCountersWidget(QFrame):
    """Widget para mostrar y editar contadores de alquimias por tipo y total de cords"""
    
    alchemyChanged = pyqtSignal(str, int)  # (alchemy_type, new_count)
    
    ALCHEMY_TYPES = [
        ('diamante', '💎 Diamante', '#87CEEB'),
        ('rubi', '🔴 Rubí', '#DC143C'),
        ('jade', '🟢 Jade', '#00C957'),
        ('zafiro', '🔵 Zafiro', '#4169E1'),
        ('granate', '🟤 Granate', '#A52A2A'),
        ('onice', '⚫ Ónice', '#2F4F4F'),
    ]

    def __init__(self, controller=None, event_id=None):
        super().__init__()
        self.controller = controller
        self.event_id = event_id
        self.spinboxes = {}
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border: 2px solid #5d4d2b;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)
        
        # === SECCION CORDS TOTALES ===
        cords_section = QFrame()
        cords_section.setStyleSheet("""
            QFrame {
                background-color: #1b3a1b;
                border: 2px solid #4caf50;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        cords_layout = QVBoxLayout()
        cords_layout.setContentsMargins(10, 8, 10, 8)
        cords_layout.setSpacing(5)
        cords_section.setLayout(cords_layout)
        
        cords_title = QLabel("📦 CORDS TOTALES")
        cords_title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #4caf50;
            border: none;
        """)
        cords_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cords_layout.addWidget(cords_title)
        
        self.lbl_total_cords = QLabel("0")
        self.lbl_total_cords.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            color: #00ff00;
            border: none;
        """)
        self.lbl_total_cords.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cords_layout.addWidget(self.lbl_total_cords)
        
        main_layout.addWidget(cords_section)
        
        # === SEPARADOR ===
        separator = QFrame()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #5d4d2b; border: none;")
        main_layout.addWidget(separator)
        
        # === SECCION ALQUIMIAS ===
        title = QLabel("🧪 ALQUIMIAS")
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #d4af37; 
            text-shadow: 1px 1px black;
            border: none;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Grid de contadores
        grid = QGridLayout()
        grid.setSpacing(10)
        
        for i, (alchemy_type, display_name, color) in enumerate(self.ALCHEMY_TYPES):
            row = i // 3
            col = i % 3
            
            # Container para cada alquimia
            container = QFrame()
            container.setStyleSheet(f"""
                QFrame {{
                    background-color: #252540;
                    border: 1px solid {color};
                    border-radius: 6px;
                    padding: 5px;
                }}
            """)
            container_layout = QVBoxLayout()
            container_layout.setContentsMargins(8, 5, 8, 5)
            container_layout.setSpacing(5)
            container.setLayout(container_layout)
            
            # Label
            lbl = QLabel(display_name)
            lbl.setStyleSheet(f"""
                color: {color}; 
                font-weight: bold; 
                font-size: 12px;
                border: none;
            """)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(lbl)
            
            # Controles: - [SpinBox] +
            controls = QHBoxLayout()
            controls.setSpacing(5)
            
            btn_minus = QPushButton("-")
            btn_minus.setFixedSize(24, 24)
            btn_minus.setStyleSheet("""
                QPushButton {
                    background-color: #550000;
                    color: white;
                    border: 1px solid #800000;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #800000;
                }
            """)
            
            spinbox = QSpinBox()
            spinbox.setRange(0, 9999)
            spinbox.setFixedWidth(60)
            spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spinbox.setStyleSheet("""
                QSpinBox {
                    background-color: #1a1a1a;
                    color: #e0e0e0;
                    border: 1px solid #5d4d2b;
                    border-radius: 3px;
                    padding: 2px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    width: 0;
                }
            """)
            self.spinboxes[alchemy_type] = spinbox
            
            btn_plus = QPushButton("+")
            btn_plus.setFixedSize(24, 24)
            btn_plus.setStyleSheet("""
                QPushButton {
                    background-color: #1b5e20;
                    color: white;
                    border: 1px solid #2e7d32;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2e7d32;
                }
            """)
            
            # Conectar señales
            btn_minus.clicked.connect(lambda checked, sb=spinbox: sb.setValue(sb.value() - 1))
            btn_plus.clicked.connect(lambda checked, sb=spinbox: sb.setValue(sb.value() + 1))
            spinbox.valueChanged.connect(lambda val, at=alchemy_type: self._on_value_changed(at, val))
            
            controls.addWidget(btn_minus)
            controls.addWidget(spinbox)
            controls.addWidget(btn_plus)
            container_layout.addLayout(controls)
            
            grid.addWidget(container, row, col)
        
        main_layout.addLayout(grid)
        
        # Total Alquimias
        self.lbl_total = QLabel("TOTAL: 0")
        self.lbl_total.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffd700;
            border: none;
            margin-top: 5px;
        """)
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_total)

    def _on_value_changed(self, alchemy_type, value):
        """Llamado cuando cambia el valor de un spinbox"""
        if self.controller and self.event_id:
            self.controller.update_alchemy_count(self.event_id, alchemy_type, value)
        
        self._update_alchemy_total()
        self.alchemyChanged.emit(alchemy_type, value)

    def _update_alchemy_total(self):
        """Actualiza el label de total de alquimias"""
        total = sum(sb.value() for sb in self.spinboxes.values())
        self.lbl_total.setText(f"TOTAL: {total}")

    def _update_cords_total(self):
        """Actualiza el label de total de cords de la jornada"""
        if not self.controller or not self.event_id:
            self.lbl_total_cords.setText("0")
            return
            
        # Obtener la suma de todos los cords de todas las cuentas del evento
        cords_summary = self.controller.get_event_cords_summary(self.event_id)
        total_cords = sum(cords_summary.values())
        self.lbl_total_cords.setText(str(total_cords))

    def load_data(self):
        """Carga los datos del evento actual"""
        if not self.controller or not self.event_id:
            self.lbl_total_cords.setText("0")
            return
            
        # Cargar alquimias
        counters = self.controller.get_alchemy_counters(self.event_id)
        
        # Bloquear señales mientras cargamos
        for alchemy_type, spinbox in self.spinboxes.items():
            spinbox.blockSignals(True)
            spinbox.setValue(counters.get(alchemy_type, 0))
            spinbox.blockSignals(False)
        
        self._update_alchemy_total()
        self._update_cords_total()

    def set_event(self, event_id):
        """Cambia el evento y recarga los datos"""
        self.event_id = event_id
        self.load_data()

    def refresh(self):
        """Recarga los datos del evento actual"""
        self.load_data()

    def update_cords_display(self):
        """Actualiza solo el display de cords (llamar cuando cambian cords en las filas)"""
        self._update_cords_total()

