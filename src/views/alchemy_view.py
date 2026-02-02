from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                             QFrame, QGroupBox, QGridLayout, QSpinBox, QListWidget, QSplitter, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from src.controllers.alchemy_controller import AlchemyController
from src.views.widgets.daily_grid import DailyGridWidget

class AlchemyRow(QFrame):
    """ Fila individual: Cuenta | Slots | PJ | Grid """
    def __init__(self, char_data, controller):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: #263238; border-radius: 4px; margin-bottom: 2px;")
        
        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.setLayout(layout)

        # 1. Nombre Cuenta (Ej: ALOLA)
        lbl_account = QLabel(char_data['account'].username)
        lbl_account.setFixedWidth(120)
        lbl_account.setStyleSheet("color: #b0bec5; font-weight: bold; font-size: 12px;")
        
        # 2. Cantidad Slots (Ej: 5)
        spin_slots = QSpinBox()
        spin_slots.setValue(5)
        spin_slots.setRange(1, 10)
        spin_slots.setFixedWidth(40)
        spin_slots.setStyleSheet("background-color: #37474f; color: white; border: none;")

        # 3. Nombre Personaje (Ej: Tabacman)
        lbl_char = QLabel(char_data['character'].name)
        lbl_char.setFixedWidth(120)
        lbl_char.setStyleSheet("color: #4dd0e1; font-weight: bold; font-size: 13px;")
        
        # 4. Grid de Botones
        # Conectamos la señal de cambio de estado al controlador
        grid_widget = DailyGridWidget(char_data['activity'])
        
        # Usamos una lambda o functools.partial para capturar el char_id
        char_id = char_data['character'].id
        grid_widget.statusChanged.connect(lambda day, status, cid=char_id: controller.update_daily_status(cid, day, status))
        
        # (Widget, Fila, Columna)
        layout.addWidget(lbl_account, 0, 0)
        layout.addWidget(spin_slots, 0, 1)
        layout.addWidget(lbl_char, 0, 2)
        layout.addWidget(grid_widget, 0, 3)
        
        layout.setColumnStretch(3, 1) 

class StoreDetailsWidget(QWidget):
    """ Widget que muestra el contenido de una tienda seleccionada """
    def __init__(self, store_data, controller):
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        
        # Título de la tienda
        title = QLabel(f"📧 {store_data['store'].email}")
        title.setStyleSheet("font-size: 18px; color: #ffca28; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Filas de personajes
        for row_data in store_data['rows']:
            row_widget = AlchemyRow(row_data, controller)
            layout.addWidget(row_widget)

class AlchemyView(QWidget):
    # Señal para volver al inicio
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = AlchemyController()
        # Cacheamos los datos
        self.data = [] 
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Splitter para dividir Left/Right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- PANEL IZQUIERDO (Lista de Tiendas) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Botón Volver
        btn_back = QPushButton("← Volver")
        btn_back.clicked.connect(self.backRequested.emit)
        btn_back.setStyleSheet("""
            QPushButton {
                 background-color: transparent; color: #b0bec5; 
                 font-size: 14px; border: none; text-align: left;
            }
            QPushButton:hover { color: white; }
        """)
        left_layout.addWidget(btn_back)
        
        left_title = QLabel(f"Cuentas ({self.server_name})")
        left_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #eceff1; margin-top: 10px;")
        left_layout.addWidget(left_title)
        
        self.store_list = QListWidget()
        self.store_list.setStyleSheet("""
            QListWidget {
                background-color: #263238;
                border: 1px solid #37474f;
                color: #b0bec5;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #00bcd4;
                color: white;
            }
        """)
        self.store_list.itemClicked.connect(self.on_store_selected)
        left_layout.addWidget(self.store_list)
        
        # --- PANEL DERECHO (Detalles) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        right_title = QLabel("Detalle de Cors")
        right_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #eceff1;")
        right_layout.addWidget(right_title)
        
        # Scroll Area para los detalles
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #102027; }")
        
        # Placeholder inicial
        self.details_container = QWidget()
        self.details_container.setStyleSheet("background-color: #102027;")
        self.details_layout = QVBoxLayout()
        self.details_container.setLayout(self.details_layout)
        
        self.scroll.setWidget(self.details_container)
        right_layout.addWidget(self.scroll)

        # Agregar widgets al splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Proporción inicial (30% izquierda, 70% derecha)
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        
        # Cargar datos
        self.load_data()

    def load_data(self):
        self.data = self.controller.get_alchemy_dashboard_data(self.server_id)
        self.store_list.clear()
        
        for store_entry in self.data:
            email = store_entry['store'].email
            # Usamos el email como texto del item
            self.store_list.addItem(email)
            
    def on_store_selected(self, item):
        email = item.text()
        
        # Buscar los datos correspondientes
        selected_store_data = next((d for d in self.data if d['store'].email == email), None)
        
        if selected_store_data:
            # Limpiar panel derecho
            self.clear_details()
            
            # Crear y agregar el widget de detalle
            details = StoreDetailsWidget(selected_store_data, self.controller)
            self.details_layout.addWidget(details)
            self.details_layout.addStretch() # Empujar contenido arriba

    def clear_details(self):
        # Eliminar todos los widgets del layout de detalles
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

