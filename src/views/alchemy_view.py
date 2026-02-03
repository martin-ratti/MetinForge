from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                             QFrame, QGroupBox, QGridLayout, QSpinBox, QListWidget, QSplitter,
                             QPushButton, QInputDialog, QMessageBox, QListWidgetItem, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from src.controllers.alchemy_controller import AlchemyController
from src.views.widgets.daily_grid import DailyGridWidget
import datetime

class AlchemyRow(QFrame):
    """ Fila individual: Cuenta | Slots | PJ Principal | Grid """
    editRequested = pyqtSignal(object) # game_account object

    def __init__(self, game_account, controller, event_id, total_days):
        super().__init__()
        self.game_account = game_account
        self.controller = controller
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: #263238; border-radius: 4px; margin-bottom: 2px;")
        
        # Use QHBoxLayout to match Header
        layout = QHBoxLayout()
        # Margins: Left, Top, Right, Bottom
        # We use consistent margins
        layout.setContentsMargins(5, 5, 5, 5) 
        layout.setSpacing(10)
        self.setLayout(layout)

        # 3. Nombre Personaje (Principal/Visual)
        first_char = game_account.characters[0] if game_account.characters else None

        # Grid Activity Map
        activity_map = getattr(game_account, 'current_event_activity', {})
        
        from src.views.widgets.daily_grid import DailyGridWidget
        grid_widget = DailyGridWidget(activity_map, total_days=total_days)
        
        # Connect signals
        if first_char:
            char_id = first_char.id
            grid_widget.statusChanged.connect(
                lambda day, status, cid=char_id, eid=event_id: 
                controller.update_daily_status(cid, day, status, event_id=eid)
            )

        # 1. Nombre Cuenta
        lbl_account = QLabel(game_account.username)
        lbl_account.setFixedWidth(150)
        lbl_account.setStyleSheet("color: #b0bec5; font-weight: bold; font-size: 12px;")
        
        # 2. Cantidad Slots
        real_slots = len(game_account.characters)
        lbl_slots = QLabel(str(real_slots))
        lbl_slots.setFixedWidth(40)
        lbl_slots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_slots.setStyleSheet("background-color: #37474f; color: #eceff1; border-radius: 2px; padding: 2px;")

        # 3. Nombre Personaje
        char_name = first_char.name if first_char else "-"
        display_name = char_name.split('_')[0] if '_' in char_name else char_name
        
        lbl_char = QLabel(display_name)
        lbl_char.setFixedWidth(150)
        lbl_char.setStyleSheet("color: #4dd0e1; font-weight: bold; font-size: 13px;")
        
        layout.addWidget(lbl_account)
        layout.addWidget(lbl_slots)
        layout.addWidget(lbl_char)
        layout.addWidget(grid_widget, 1) # Stretch factor 1 to take remaining space
        
    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        action_edit = menu.addAction("✏️ Editar Cuenta")
        action = menu.exec(event.globalPos())
        if action == action_edit:
            self.editRequested.emit(self.game_account)

class StoreDetailsWidget(QWidget):
    def __init__(self, store_data, controller, view_parent, event_id, total_days):
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        # Título
        title_widget = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 0, 5) 
        title_widget.setLayout(title_layout)
        title = QLabel(f"📧 {store_data['store'].email}")
        title.setStyleSheet("font-size: 18px; color: #ffca28; font-weight: bold;")
        title_layout.addWidget(title)
        layout.addWidget(title_widget)
        
        # --- HEADER ---
        # Must match AlchemyRow layout EXACTLY
        header_container = QWidget()
        header_layout = QHBoxLayout()
        # Match AlchemyRow margins: (5, 5, 5, 5) - but here maybe just 0 vertical padding? 
        # Using (5, 0, 5, 0) might cause width mismatch if AlchemyRow QFrame has borders.
        # AlchemyRow has stylesheet border-radius 4px. Usually border 0 unless specified.
        # Let's try to match horizontal margins exactly.
        header_layout.setContentsMargins(5, 5, 5, 5) 
        header_layout.setSpacing(10)
        header_container.setLayout(header_layout)
        
        lbl_h1 = QLabel("CUENTA")
        lbl_h1.setFixedWidth(150)
        lbl_h1.setStyleSheet("color: #757575; font-size: 10px; font-weight: bold;")
        
        lbl_h2 = QLabel("SLOTS")
        lbl_h2.setFixedWidth(40)
        lbl_h2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_h2.setStyleSheet("color: #757575; font-size: 10px; font-weight: bold;")
        
        lbl_h3 = QLabel("PERSONAJE")
        lbl_h3.setFixedWidth(150)
        lbl_h3.setStyleSheet("color: #757575; font-size: 10px; font-weight: bold;")
        
        header_layout.addWidget(lbl_h1)
        header_layout.addWidget(lbl_h2)
        header_layout.addWidget(lbl_h3)
        
        from src.views.widgets.daily_grid import DailyGridHeaderWidget
        header_grid = DailyGridHeaderWidget(total_days=total_days)
        header_layout.addWidget(header_grid, 1) # Stretch factor 1
        
        layout.addWidget(header_container)
        
        # Cuentas
        accounts = store_data.get('accounts', [])
        for game_account in accounts:
            row_widget = AlchemyRow(game_account, controller, event_id, total_days)
            row_widget.editRequested.connect(view_parent.on_edit_account_requested)
            layout.addWidget(row_widget)

class AlchemyView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = AlchemyController()
        
        self.data = [] 
        self.selected_email = None
        self.current_event = None
        self.events_cache = []

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT PANEL ---
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        header_left = QHBoxLayout()
        header_left.setSpacing(10)
        
        btn_back = QPushButton("←")
        btn_back.setFixedWidth(40)
        btn_back.setFixedHeight(30)
        btn_back.clicked.connect(self.backRequested.emit)
        btn_back.setStyleSheet("QPushButton { background-color: #263238; color: #b0bec5; border: 1px solid #37474f; border-radius: 4px; font-weight: bold; font-size: 16px; } QPushButton:hover { background-color: #37474f; color: white; }")
        
        left_title = QLabel(f"{self.server_name}")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d4af37;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        left_layout.addLayout(header_left)
        
        btn_add_email = QPushButton("Agregar Correo") 
        btn_add_email.setFixedWidth(140)
        btn_add_email.setFixedHeight(30)
        btn_add_email.clicked.connect(self.prompt_add_email)
        btn_add_email.setStyleSheet("QPushButton { background-color: #1565c0; color: white; border: 1px solid #1e88e5; border-radius: 4px; font-weight: bold; font-size: 13px; } QPushButton:hover { background-color: #1e88e5; }")
        
        email_toolbar = QHBoxLayout()
        email_toolbar.addWidget(btn_add_email)
        email_toolbar.addStretch()
        left_layout.addLayout(email_toolbar)
        
        self.store_list = QListWidget()
        self.store_list.setStyleSheet("""
            QListWidget { background-color: #263238; border: 1px solid #37474f; color: #b0bec5; font-size: 13px; outline: none; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #37474f; }
            QListWidget::item:selected { background-color: #3e2723; color: #ffca28; border-left: 4px solid #ffca28; }
            QListWidget::item:hover { background-color: #303030; }
        """)
        self.store_list.itemClicked.connect(self.on_store_selected)
        left_layout.addWidget(self.store_list)
        
        # --- RIGHT PANEL ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        header_right = QHBoxLayout()
        header_right.setSpacing(10)
        
        lbl_server = QLabel(f"{self.server_name.upper()}")
        lbl_server.setStyleSheet("font-size: 20px; font-weight: bold; color: #eceff1;")
        header_right.addWidget(lbl_server)
        
        header_right.addStretch()
        
        # Eventos
        self.combo_events = QComboBox()
        self.combo_events.setMinimumWidth(200)
        self.combo_events.setStyleSheet("padding: 5px; background-color: #37474f; color: white; border: 1px solid #546e7a; border-radius: 4px;")
        self.combo_events.currentIndexChanged.connect(self.on_event_changed)
        header_right.addWidget(self.combo_events)
        
        self.btn_new_event = QPushButton("➕ Nueva Jornada")
        self.btn_new_event.clicked.connect(self.prompt_create_event)
        self.btn_new_event.setStyleSheet("background-color: #f57f17; color: white; border-radius: 4px; font-weight: bold; padding: 5px 10px;")
        header_right.addWidget(self.btn_new_event)
        
        header_right.addSpacing(20)
        
        self.btn_add_account = QPushButton("👤+ Crear Cuenta")
        self.btn_add_account.setFixedHeight(30)
        self.btn_add_account.setVisible(False)
        self.btn_add_account.clicked.connect(self.prompt_add_game_account)
        self.btn_add_account.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 14px; padding: 0 10px; } QPushButton:hover { background-color: #388e3c; }")

        header_right.addWidget(self.btn_add_account)
        right_layout.addLayout(header_right)
        
        # Headers del Grid (REMOVED - Now inside StoreDetailsWidget)
        # self.header_frame = QFrame()
        # ...
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #102027; }")
        
        self.details_container = QWidget()
        self.details_container.setStyleSheet("background-color: #102027;")
        self.details_layout = QVBoxLayout()
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_container.setLayout(self.details_layout)
        
        self.scroll.setWidget(self.details_container)
        right_layout.addWidget(self.scroll)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)
        
        self.load_events()

    def load_events(self):
        self.events_cache = self.controller.get_alchemy_events(self.server_id)
        self.combo_events.blockSignals(True)
        self.combo_events.clear()
        
        if not self.events_cache:
            self.combo_events.addItem("--- Sin Jornadas ---")
            self.current_event = None
        else:
            for ev in self.events_cache:
                self.combo_events.addItem(ev.name, ev)
            
            self.combo_events.setCurrentIndex(0)
            self.current_event = self.events_cache[0]
            
        self.combo_events.blockSignals(False)
        # self.rebuild_header() # Removed
        self.load_data()

    def prompt_create_event(self):
        from src.views.dialogs.event_dialog import EventDialog
        dialog = EventDialog(self)
        # Pre-fill name suggestion
        dialog.txt_name.setText(f"Evento {len(self.events_cache) + 1}")
        
        if dialog.exec():
            name, days = dialog.get_data()
            if not name: return
            
            new_ev = self.controller.create_alchemy_event(self.server_id, name, days)
            if new_ev:
                self.load_events()
                # Select the new event
                index = self.combo_events.findData(new_ev)
                if index >= 0:
                    self.combo_events.setCurrentIndex(index)
            else:
                QMessageBox.warning(self, "Error", "No se pudo crear el evento.")

    def on_event_changed(self, index):
        if index < 0: return
        self.current_event = self.combo_events.itemData(index)
        # self.rebuild_header() # Removed
        self.load_data(preserve_selection=self.selected_email)

    # rebuild_header Removed

    def load_data(self, preserve_selection=None):
        if not self.current_event:
            self.data = []
            self.store_list.clear() 
            self.clear_details()
            return

        self.data = self.controller.get_alchemy_dashboard_data(self.server_id, event_id=self.current_event.id)
        
        self.store_list.clear() 
        self.clear_details()
        self.btn_add_account.setVisible(False)
        self.selected_email = None
        
        for entry in self.data:
             self.store_list.addItem(entry['store'].email)
        
        if preserve_selection:
            exists = any(d['store'].email == preserve_selection for d in self.data)
            if exists:
                items = self.store_list.findItems(preserve_selection, Qt.MatchFlag.MatchExactly)
                if items:
                    self.store_list.setCurrentItem(items[0])
                    self.on_store_selected(items[0])

    def on_store_selected(self, item):
        email = item.text()
        self.selected_email = email
        self.btn_add_account.setVisible(True)
        
        selected_store_data = next((d for d in self.data if d['store'].email == email), None)
        
        if selected_store_data:
            self.clear_details()
            total = self.current_event.total_days if self.current_event else 31
            eid = self.current_event.id if self.current_event else None
            details = StoreDetailsWidget(selected_store_data, self.controller, self, eid, total)
            self.details_layout.addWidget(details)
            self.details_layout.addStretch()

    def clear_details(self):
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def prompt_add_email(self):
        email, ok = QInputDialog.getText(self, "Nuevo Correo", "Dirección de Email:")
        if ok and email:
            email = email.strip()
            if self.controller.create_store_email(email):
                QMessageBox.information(self, "Éxito", f"Correo '{email}' agregado.")
                self.load_data(preserve_selection=email)
            else:
                 QMessageBox.warning(self, "Error", "No se pudo crear el correo.")

    def prompt_add_game_account(self):
        if not self.selected_email: return
        from src.views.dialogs.account_dialog import AccountDialog
        dialog = AccountDialog(self, email=self.selected_email)
        dialog.txt_email.setReadOnly(True)
        
        if dialog.exec():
            _, username, pj_name, slots = dialog.get_data()
            if self.controller.create_game_account(self.server_id, username, slots, self.selected_email, pj_name):
                 QMessageBox.information(self, "Éxito", "Cuenta creada.")
                 self.load_data(preserve_selection=self.selected_email)
            else:
                 QMessageBox.warning(self, "Error", "Error al crear cuenta.")

    def on_edit_account_requested(self, game_account):
        first_char = game_account.characters[0] if game_account.characters else None
        current_pj_name = first_char.name.split('_')[0] if first_char else ""
        from src.views.dialogs.account_dialog import AccountDialog
        current_slots = len(game_account.characters)
        current_email = game_account.store_account.email
        
        dialog = AccountDialog(self, username=game_account.username, slots=current_slots, email=current_email, edit_mode=True)
        dialog.txt_pj_name.setText(current_pj_name)
        
        if dialog.exec():
            new_email, new_name, new_pj_name, new_slots = dialog.get_data()
            if self.controller.update_game_account(game_account.id, new_name, new_slots, new_email):
                 QMessageBox.information(self, "Éxito", "Cuenta actualizada.")
                 self.load_data(preserve_selection=new_email)
            else:
                 QMessageBox.warning(self, "Error", "No se pudo actualizar.")
