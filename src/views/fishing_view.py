from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                             QFrame, QPushButton, QComboBox, QSplitter, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from src.controllers.fishing_controller import FishingController
import datetime

# --- WIDGETS ---

class WeekButton(QPushButton):
    statusChanged = pyqtSignal(int, int, int) # month, week, new_status

    def __init__(self, month, week, status=0):
        super().__init__()
        self.month = month
        self.week = week
        self.status = status
        self.setFixedSize(25, 25)
        self.update_style()
        self.clicked.connect(self.toggle_status)

    def toggle_status(self):
        # 0 -> 1 -> -1 -> 0
        if self.status == 0: self.status = 1
        elif self.status == 1: self.status = -1
        else: self.status = 0
        self.update_style()
        self.statusChanged.emit(self.month, self.week, self.status)

    def update_style(self):
        base_style = "border: none; border-radius: 4px; font-weight: bold; font-size: 14px;"
        if self.status == 1:
            self.setText("🐟") 
            self.setStyleSheet(f"background-color: #4fc3f7; color: white; {base_style}")
        elif self.status == -1:
            self.setText("✕")
            self.setStyleSheet(f"background-color: #ef5350; color: white; {base_style}")
        else:
            self.setText("")
            self.setStyleSheet(f"background-color: #37474f; {base_style}")

class FishingGridWidget(QWidget):
    cellStatusChanged = pyqtSignal(int, int, int) # m, w, status

    def __init__(self, activity_map, year):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)
        
        for m in range(1, 13):
            month_frame = QFrame()
            month_frame.setStyleSheet("border-left: 1px solid #5d4d2b;") 
            mf_layout = QHBoxLayout()
            mf_layout.setContentsMargins(2, 0, 2, 0)
            mf_layout.setSpacing(2)
            month_frame.setLayout(mf_layout)
            
            for w in range(1, 5):
                key = f"{m}_{w}"
                st = activity_map.get(key, 0)
                btn = WeekButton(m, w, st)
                btn.statusChanged.connect(self.cellStatusChanged.emit)
                mf_layout.addWidget(btn)
            
            self.layout.addWidget(month_frame)

class FishingRow(QFrame):
    def __init__(self, game_account, controller, year):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        # Metin2 Palette: Dark Bg #1a1a1a, Gold Border #5d4d2b
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a; 
                border: 1px solid #5d4d2b; 
                border-radius: 4px; 
                margin-bottom: 2px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # 1st Char as representative
        first_char = game_account.characters[0] if game_account.characters else None
        char_name = first_char.name if first_char else "???"
        display_name = char_name.split('_')[0] if '_' in char_name else char_name

        # Account Name
        lbl_acc = QLabel(game_account.username)
        lbl_acc.setFixedWidth(120)
        # Metin Text (Grey/White)
        lbl_acc.setStyleSheet("border: none; color: #e0e0e0; font-weight: bold;")
        layout.addWidget(lbl_acc)

        # Char Name (Pescador)
        lbl_name = QLabel(display_name)
        lbl_name.setFixedWidth(120)
        # Metin Gold Text
        lbl_name.setStyleSheet("border: none; color: #d4af37; font-weight: bold;")
        layout.addWidget(lbl_name)
        
        # Grid
        activity_map = getattr(game_account, 'fishing_activity_map', {})
        self.grid = FishingGridWidget(activity_map, year)
        
        # Connect
        if first_char:
            self.grid.cellStatusChanged.connect(lambda m, w, s: controller.update_fishing_status(first_char.id, year, m, w, s))
        
        layout.addWidget(self.grid)
        layout.addStretch()

class FishingHeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)
        
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        for m_name in months:
            m_frame = QFrame()
            m_frame.setStyleSheet("border-left: 1px solid #5d4d2b; background-color: #2b1d0e;")
            mf_layout = QVBoxLayout()
            mf_layout.setContentsMargins(2, 2, 2, 2)
            mf_layout.setSpacing(0)
            m_frame.setLayout(mf_layout)
            
            # Month Label
            lbl_m = QLabel(m_name)
            lbl_m.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_m.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 10px; border: none;")
            mf_layout.addWidget(lbl_m)
            
            # Weeks Row
            weeks_layout = QHBoxLayout()
            weeks_layout.setSpacing(2)
            for i in range(1, 5):
                lbl_w = QLabel(str(i))
                lbl_w.setFixedSize(25, 15)
                lbl_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_w.setStyleSheet("color: #a0a0a0; font-size: 9px; border: none;")
                weeks_layout.addWidget(lbl_w)
            
            mf_layout.addLayout(weeks_layout)
            layout.addWidget(m_frame)

class FishingStoreDetailsWidget(QWidget):
    def __init__(self, store_data, controller, year):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        # Título Corre
        title_widget = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 0, 5) 
        title_widget.setLayout(title_layout)
        title = QLabel(f"📧 {store_data['store'].email}")
        title.setStyleSheet("font-size: 18px; color: #d4af37; font-weight: bold; text-shadow: 1px 1px black;")
        title_layout.addWidget(title)
        layout.addWidget(title_widget)
        
        # Header Annual
        header_container = QWidget()
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(5, 0, 5, 0)
        h_layout.setSpacing(10)
        header_container.setLayout(h_layout)
        
        lbl_h_acc = QLabel("CUENTA")
        lbl_h_acc.setFixedWidth(120)
        lbl_h_acc.setStyleSheet("color: #a0a0a0; font-weight: bold;")
        h_layout.addWidget(lbl_h_acc)
        
        lbl_h1 = QLabel("PESCADOR")
        lbl_h1.setFixedWidth(120) 
        lbl_h1.setStyleSheet("color: #a0a0a0; font-weight: bold;")
        h_layout.addWidget(lbl_h1)
        
        grid_header = FishingHeaderWidget()
        h_layout.addWidget(grid_header)
        h_layout.addStretch()
        layout.addWidget(header_container)

        # Cuentas 
        accounts = store_data.get('accounts', [])
        for game_account in accounts:
             row = FishingRow(game_account, controller, year)
             layout.addWidget(row)


# --- MAIN VIEW ---

class FishingView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = FishingController()
        self.current_year = datetime.date.today().year
        self.data_cache = []
        self.selected_store_email = None

        self.init_ui()
        self.load_data()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT PANEL: Stores List ---
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Header Left
        header_left = QHBoxLayout()
        btn_back = QPushButton("←")
        btn_back.setFixedWidth(40)
        btn_back.clicked.connect(self.backRequested.emit)
        btn_back.setStyleSheet("QPushButton { background-color: #263238; color: #b0bec5; font-weight: bold; }")
        
        left_title = QLabel("Pesca Anual")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d4af37;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        left_layout.addLayout(header_left)
        
        # Store List
        self.store_list = QListWidget()
        self.store_list.setStyleSheet("""
            QListWidget { background-color: #263238; border: 1px solid #37474f; color: #b0bec5; font-size: 13px; outline: none; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #37474f; }
            QListWidget::item:selected { background-color: #3e2723; color: #ffca28; border-left: 4px solid #ffca28; }
            QListWidget::item:hover { background-color: #303030; }
        """)
        self.store_list.itemClicked.connect(self.on_store_selected)
        left_layout.addWidget(self.store_list)
        
        # --- RIGHT PANEL: Details ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # Top Bar Right
        top_bar = QHBoxLayout()
        lbl_server = QLabel(f"{self.server_name.upper()}")
        lbl_server.setStyleSheet("font-size: 20px; font-weight: bold; color: #eceff1;")
        
        self.combo_year = QComboBox()
        for y in range(2025, 2031):
            self.combo_year.addItem(str(y))
        self.combo_year.setCurrentText(str(self.current_year))
        self.combo_year.setStyleSheet("padding: 5px; background-color: #37474f; color: white;")
        self.combo_year.currentIndexChanged.connect(self.on_year_changed)
        
        top_bar.addWidget(lbl_server)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Año:"))
        top_bar.addWidget(self.combo_year)
        right_layout.addLayout(top_bar)
        
        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True) # Vertical resize
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #102027; }")
        
        self.content_container = QWidget()
        self.content_container.setStyleSheet("background-color: #102027;")
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_container.setLayout(self.content_layout)
        
        self.scroll.setWidget(self.content_container)
        right_layout.addWidget(self.scroll)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)

    def load_data(self):
        self.data_cache = self.controller.get_fishing_data(self.server_id, self.current_year)
        
        # Populate List
        self.store_list.clear()
        selected_item = None
        
        for store_data in self.data_cache:
            store = store_data['store']
            item = QListWidgetItem(store.email)
            item.setData(Qt.ItemDataRole.UserRole, store_data)
            self.store_list.addItem(item)
            
            if self.selected_store_email == store.email:
                selected_item = item
        
        if selected_item:
            self.store_list.setCurrentItem(selected_item)
            self.show_store_details(selected_item.data(Qt.ItemDataRole.UserRole))
        elif self.store_list.count() > 0:
            self.store_list.setCurrentRow(0)
            self.show_store_details(self.store_list.item(0).data(Qt.ItemDataRole.UserRole))
        else:
            self.clear_details()

    def on_store_selected(self, item):
        store_data = item.data(Qt.ItemDataRole.UserRole)
        self.selected_store_email = store_data['store'].email
        self.show_store_details(store_data)

    def show_store_details(self, store_data):
        # Clear right panel
        self.clear_details()
        
        details_widget = FishingStoreDetailsWidget(store_data, self.controller, self.current_year)
        self.content_layout.addWidget(details_widget)
        
    def clear_details(self):
        while self.content_layout.count():
             item = self.content_layout.takeAt(0)
             if item.widget(): item.widget().deleteLater()

    def on_year_changed(self):
        self.current_year = int(self.combo_year.currentText())
        self.load_data()
