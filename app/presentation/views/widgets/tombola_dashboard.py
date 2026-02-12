import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QSpinBox, QScrollArea,
                             QFrame, QPushButton)

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
        
        # Image for Day Prize
        lbl_dp_img = QLabel()
        # Removed setFixedSize to allow image to determine size (up to scaled limit)
        lbl_dp_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_dp_img.setStyleSheet("background-color: transparent; border: none;")
        
        dp_img_path = os.path.join(os.getcwd(), 'app', 'presentation', 'assets', 'images', 'tombola', 'day_prize.png')
        if os.path.exists(dp_img_path):
            dp_pixmap = QPixmap(dp_img_path)
            # Scale to smaller dimensions but keep aspect ratio (e.g., 80x80 max)
            lbl_dp_img.setPixmap(dp_pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        # Layout for Image + Title
        dp_header_layout = QVBoxLayout()
        dp_header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dp_header_layout.addWidget(lbl_dp_img, 0, Qt.AlignmentFlag.AlignCenter)
        dp_header_layout.addWidget(day_prize_title, 0, Qt.AlignmentFlag.AlignCenter)
        
        day_prize_layout.addLayout(dp_header_layout)
        
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
            [
                ("Viento", "talisman_wind.png"),
                ("Tierra", "talisman_earth.png"),
                ("Hielo", "talisman_ice.png"),
                ("Fuego", "talisman_fire.png"),
                ("Oscuridad", "talisman_dark.png"),
                ("Rayo", "talisman_lightning.png")
            ],
            color="#4fc3f7" # Light Blue
        )
        self.content_layout.addWidget(self.group_talismans)
        
        # 2. Premios
        self.group_prizes = self.create_counter_group(
            "PREMIOS", 
            [
                ("Dioxido", "titanium_dioxide.png"),
                ("Adularia", "moonstone.png"), 
                ("Jadita noche", "night_jade.png"), 
                ("Refinados", "refined.png"), 
                ("Caja carta monstruo plata", "silver_okey_chest.png"), 
                ("Baúl habilidad", "skill_book_chest.png"), 
                ("Cofre manual mascota", "pet_book_chest.png"), 
                ("Alubia Verde", "green_dragon_bean.png"), 
                ("Hierba dorada", "golden_herb.png"), 
                ("Ágata", "agate.png")
            ],
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
                border: 2px solid #5d4d2b;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                font-size: 13px;
                color: {color};
                background-color: #202020;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(10, 15, 10, 10)
        
        # items is now list of tuples: (name, image_filename)
        for i, (item_name, image_file) in enumerate(items):
            row = i // 2
            col = i % 2
            
            # Container for each item
            item_container = QFrame()
            item_container.setStyleSheet("""
                QFrame {
                    background-color: #2b2b2b;
                    border: 1px solid #3e2723;
                    border-radius: 8px;
                    padding: 4px;
                }
                QFrame:hover {
                    border: 1px solid #d4af37;
                    background-color: #3e3e3e;
                }
            """)
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(8, 6, 8, 6)
            item_layout.setSpacing(10)
            item_container.setLayout(item_layout)

            # Image
            lbl_img = QLabel()
            # Removed setFixedSize to allow image to expand naturally
            lbl_img.setMinimumSize(48, 48) 
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_img.setStyleSheet("background-color: transparent; border: none;") # Ensure no border on image itself
            
            # Load Image
            image_path = os.path.join(os.getcwd(), 'app', 'presentation', 'assets', 'images', 'tombola', image_file)
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                # Scale with KeepAspectRatio to prevent any distortion/cropping
                # Increased target size (e.g. 64x64) so it scales down IF needed, but doesn't get cut by a small box
                lbl_img.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                lbl_img.setText("?")
                lbl_img.setStyleSheet("color: red; font-weight: bold; font-size: 20px;")
            
            item_layout.addWidget(lbl_img)
            
            # Label
            lbl_name = QLabel(item_name)
            lbl_name.setStyleSheet("color: #e0e0e0; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            lbl_name.setWordWrap(True)
            item_layout.addWidget(lbl_name, 1) # Stretch to fill available space

            # SpinBox
            spin = NoScrollSpinBox()
            spin.setRange(0, 9999)
            spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setFixedWidth(60) # Slightly wider
            spin.setFixedHeight(30) # Taller for better touch/click target
            spin.setStyleSheet("""
                QSpinBox {
                    background-color: #1a1a1a;
                    color: #ffd700;
                    border: 1px solid #455a64;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QSpinBox:focus {
                    border: 1px solid #d4af37;
                    background-color: #000000;
                }
            """)
            
            # Fix lambda capture
            spin.valueChanged.connect(lambda val, k=item_name: self.on_counter_changed(k, val))
            self.spinboxes[item_name] = spin
            
            item_layout.addWidget(spin)
            
            grid.addWidget(item_container, row, col)
            
        group.setLayout(grid)
        return group

    def load_data(self):
        if not self.event_id:
            self.setEnabled(False)
            # Reset values
            for spin in self.spinboxes.values():
                if spin.value() != 0:
                    spin.blockSignals(True)
                    spin.setValue(0)
                    spin.blockSignals(False)
            return
            
        self.setEnabled(True)
        # Fetch counters in one go
        self.counters = self.controller.get_tombola_item_counters(self.event_id)
        
        # Batch update to prevent multiple layouts/repaints if possible (though spinboxes are independent)
        for name, spin in self.spinboxes.items():
            new_val = self.counters.get(name, 0)
            
            # Only update if value changed to avoid unnecessary signals/repaints
            if spin.value() != new_val:
                spin.blockSignals(True)
                spin.setValue(new_val)
                spin.blockSignals(False)

    def on_counter_changed(self, item_name, value):
        if not self.event_id: return
        self.controller.update_tombola_item_count(self.event_id, item_name, value)
        
    def set_event_id(self, event_id):
        self.event_id = event_id
        self.load_data()

    def update_stats(self):
        """Alias for load_data to refresh stats from DB"""
        self.load_data()
