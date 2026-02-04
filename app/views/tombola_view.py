from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                             QFrame, QListWidget, QSplitter, QPushButton, QInputDialog, QMessageBox, QListWidgetItem, QComboBox,
                             QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from app.utils.shortcuts import register_shortcuts
from app.controllers.tombola_controller import TombolaController
from app.views.widgets.daily_grid import DailyGridWidget, DailyGridHeaderWidget

class TombolaRow(QFrame):
    """Row for each game account - WITHOUT slots column"""
    selectionChanged = pyqtSignal(bool)
    rowClicked = pyqtSignal(object, Qt.KeyboardModifier)
    
    def __init__(self, game_account, controller, event_id):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.game_account = game_account
        self.controller = controller
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        # Metin2 Palette
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

        # 0. Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)

        first_char = game_account.characters[0] if game_account.characters else None

        # Grid Activity Map
        activity_map = getattr(game_account, 'current_event_activity', {})
        
        grid_widget = DailyGridWidget(activity_map, total_days=31)  # Fixed 31 days
        
        # Connect signals
        if first_char:
            char_id = first_char.id
            grid_widget.statusChanged.connect(
                lambda day, status, cid=char_id, eid=event_id: 
                controller.update_daily_status(cid, day, status, event_id=eid)
            )

        # 1. Account Name
        lbl_account = QLabel(game_account.username)
        lbl_account.setFixedWidth(150)
        lbl_account.setStyleSheet("border: none; color: #e0e0e0; font-weight: bold; font-size: 12px;")
        
        # 2. Character Name (NO SLOTS)
        char_name = first_char.name if first_char else "-"
        display_name = char_name.split('_')[0] if '_' in char_name else char_name
        
        lbl_char = QLabel(display_name)
        lbl_char.setFixedWidth(150)
        lbl_char.setStyleSheet("border: none; color: #d4af37; font-weight: bold; font-size: 13px;")
        
        lbl_account.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lbl_char.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        layout.addWidget(lbl_account)
        layout.addWidget(lbl_char)
        layout.addWidget(grid_widget, 1)

    def mousePressEvent(self, event):
        self.rowClicked.emit(self, event.modifiers())
        super().mousePressEvent(event)

    def _on_checkbox_changed(self, state):
        selected = (state == Qt.CheckState.Checked.value)
        self.update_selection_style(selected)
        self.selectionChanged.emit(selected)

    def is_selected(self):
        return self.checkbox.isChecked()

    def set_selected(self, selected):
        self.checkbox.setChecked(selected)

    def update_selection_style(self, selected):
        if selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2d2d1b;
                    border: 1px solid #d4af37;
                    border-radius: 4px;
                    margin-bottom: 2px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1a1a1a;
                    border: 1px solid #5d4d2b;
                    border-radius: 4px;
                    margin-bottom: 2px;
                }
            """)

class StoreDetailsWidget(QWidget):
    def __init__(self, store_data, controller, event_id, view_parent):
        super().__init__()
        self.controller = controller
        self.rows = []
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        # Title
        title_widget = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 0, 5) 
        title_widget.setLayout(title_layout)
        title = QLabel(f"📧 {store_data['store'].email}")
        title.setStyleSheet("font-size: 18px; color: #d4af37; font-weight: bold; text-shadow: 1px 1px black;")
        title_layout.addWidget(title)
        layout.addWidget(title_widget)
        
        # Header (WITHOUT SLOTS)
        header_container = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5) 
        header_layout.setSpacing(10)
        header_container.setLayout(header_layout)
        
        lbl_h1 = QLabel("CUENTA")
        lbl_h1.setFixedWidth(150)
        lbl_h1.setStyleSheet("color: #a0a0a0; font-size: 10px; font-weight: bold;")
        
        lbl_h3 = QLabel("PERSONAJE")
        lbl_h3.setFixedWidth(150)
        lbl_h3.setStyleSheet("color: #a0a0a0; font-size: 10px; font-weight: bold;")
        
        header_layout.addWidget(lbl_h1)
        header_layout.addWidget(lbl_h3)
        
        header_grid = DailyGridHeaderWidget(total_days=31)  # Fixed 31 days
        header_layout.addWidget(header_grid, 1)
        
        layout.addWidget(header_container)
        
        # Accounts
        accounts = store_data.get('accounts', [])
        for game_account in accounts:
            row_widget = TombolaRow(game_account, controller, event_id)
            row_widget.rowClicked.connect(view_parent.on_row_clicked)
            self.rows.append(row_widget)
            layout.addWidget(row_widget)

class TombolaView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = TombolaController()
        
        self.stores_data = []
        self.current_details_widget = None
        self.last_clicked_row = None
        
        self.init_ui()
        self.setup_shortcuts()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.load_events()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Top Bar
        top_bar = QHBoxLayout()
        
        # Back Button
        btn_back = QPushButton("← Volver")
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(self.backRequested.emit)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #550000;
                border: 2px solid #800000;
                color: #ffcccc;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #800000;
                border: 2px solid #ff4444;
            }
        """)
        top_bar.addWidget(btn_back)
        
        # Title
        lbl_title = QLabel(f"Tómbola - {self.server_name}")
        lbl_title.setStyleSheet("font-size: 20px; color: #d4af37; font-weight: bold;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(lbl_title, 1)
        
        # Event Selector
        lbl_event = QLabel("Jornada:")
        lbl_event.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        top_bar.addWidget(lbl_event)
        
        self.combo_event = QComboBox()
        self.combo_event.setFixedWidth(200)
        self.combo_event.setStyleSheet("""
            QComboBox {
                background-color: #2b2b2b;
                border: 1px solid #5d4d2b;
                color: #d4af37;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox:hover {
                border: 1px solid #d4af37;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #e0e0e0;
                selection-background-color: #5d4d2b;
            }
        """)
        self.combo_event.currentIndexChanged.connect(self.on_event_changed)
        top_bar.addWidget(self.combo_event)
        
        # Add Event Button
        btn_add_event = QPushButton("+ Nueva Jornada")
        btn_add_event.setFixedWidth(130)
        btn_add_event.clicked.connect(self.create_new_event)
        btn_add_event.setStyleSheet("""
            QPushButton {
                background-color: #2b1d0e;
                color: #d4af37;
                border: 2px solid #5d4d2b;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #3d2b1f;
                border: 2px solid #d4af37;
            }
        """)
        top_bar.addWidget(btn_add_event)
        
        # Import Button
        btn_import = QPushButton("📥 Importar")
        btn_import.setFixedWidth(100)
        btn_import.clicked.connect(self.on_import_requested)
        btn_import.setStyleSheet("""
            QPushButton {
                background-color: #455a64;
                color: white;
                border: 2px solid #607d8b;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #607d8b;
                border: 2px solid #90a4ae;
            }
        """)
        top_bar.addWidget(btn_import)

        btn_help = QPushButton("?")
        btn_help.setFixedWidth(30)
        btn_help.setFixedHeight(30)
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        btn_help.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffca28;
                border: 2px solid #ffca28;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: rgba(255, 202, 40, 0.1);
            }
        """)
        top_bar.addWidget(btn_help)
        
        layout.addLayout(top_bar)
        
        # Splitter: Store List (left) | Details (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel: Store Emails List
        self.store_list = QListWidget()
        self.store_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #5d4d2b;
                color: #e0e0e0;
                font-size: 13px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #2b2b2b;
                border: 1px solid #5d4d2b;
                border-radius: 3px;
                padding: 8px;
                margin: 3px;
            }
            QListWidget::item:selected {
                background-color: #3d2b1f;
                border: 1px solid #d4af37;
                color: #d4af37;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
        """)
        self.store_list.itemClicked.connect(self.on_store_selected)
        splitter.addWidget(self.store_list)
        
        # Right Panel: Store Details
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.details_widget.setLayout(self.details_layout)
        self.details_scroll.setWidget(self.details_widget)
        splitter.addWidget(self.details_scroll)
        
        splitter.setSizes([200, 800])
        layout.addWidget(splitter)

        # --- BATCH ACTIONS TOOLBAR ---
        self.batch_toolbar = QFrame()
        self.batch_toolbar.setFixedHeight(50)
        self.batch_toolbar.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-top: 2px solid #5d4d2b;
            }
        """)
        self.batch_toolbar.setVisible(False)
        
        batch_layout = QHBoxLayout(self.batch_toolbar)
        self.lbl_batch_count = QLabel("0 seleccionadas")
        self.lbl_batch_count.setStyleSheet("color: #d4af37; font-weight: bold;")
        batch_layout.addWidget(self.lbl_batch_count)
        
        batch_layout.addStretch()
        # Buttons
        btn_done = QPushButton("✅ Hecho (1)")
        btn_done.clicked.connect(lambda: self.apply_batch_status(1))
        btn_done.setStyleSheet("background-color: #1b5e20; color: white; border: 1px solid #4caf50; padding: 5px 15px; border-radius: 3px;")
        batch_layout.addWidget(btn_done)
        
        btn_fail = QPushButton("❌ Fallido (2)")
        btn_fail.clicked.connect(lambda: self.apply_batch_status(-1))
        btn_fail.setStyleSheet("background-color: #b71c1c; color: white; border: 1px solid #f44336; padding: 5px 15px; border-radius: 3px;")
        batch_layout.addWidget(btn_fail)
        
        btn_reset = QPushButton("♻️ Reset (3)")
        btn_reset.clicked.connect(lambda: self.apply_batch_status(0))
        btn_reset.setStyleSheet("background-color: #455a64; color: white; border: 1px solid #90a4ae; padding: 5px 15px; border-radius: 3px;")
        batch_layout.addWidget(btn_reset)
        
        layout.addWidget(self.batch_toolbar)

    def setup_shortcuts(self):
        register_shortcuts(self, {
            'Ctrl+A': self.select_all_rows,
            'Ctrl+D': self.deselect_all_rows,
            '1': lambda: self.apply_batch_status(1),
            '2': lambda: self.apply_batch_status(-1),
            '3': lambda: self.apply_batch_status(0),
        })

    def select_all_rows(self):
        if self.current_details_widget:
            for row in self.current_details_widget.rows:
                row.set_selected(True)

    def deselect_all_rows(self):
        if self.current_details_widget:
            for row in self.current_details_widget.rows:
                row.set_selected(False)

    def apply_batch_status(self, status):
        if not self.current_details_widget:
            return
            
        selected_rows = [row for row in self.current_details_widget.rows if row.is_selected()]
        if not selected_rows:
            return
            
        # Use sequential logic
        if not self.selected_event_id:
            return

        count = 0
        for row in selected_rows:
            char = row.game_account.characters[0] if row.game_account.characters else None
            if char:
                day_to_update = 1
                if status == 0:
                    # Reset logic: target last completed day
                    next_day = self.controller.get_next_pending_day(char.id, self.selected_event_id)
                    day_to_update = max(1, next_day - 1)
                else:
                    # Progress logic
                    day_to_update = self.controller.get_next_pending_day(char.id, self.selected_event_id)
                    
                self.controller.update_daily_status(
                    char.id, day_to_update, status, event_id=self.selected_event_id
                )
                count += 1
        
        
        self.load_stores() # Refresh
        QMessageBox.information(self, "Acción Batch", f"Se actualizaron {count} cuentas.")

    def on_row_clicked(self, row, modifiers):
        if not self.current_details_widget:
            return
            
        rows = self.current_details_widget.rows
        idx = rows.index(row)
        
        if modifiers & Qt.KeyboardModifier.ShiftModifier and self.last_clicked_row in rows:
            # Range selection
            start_idx = rows.index(self.last_clicked_row)
            end_idx = idx
            
            step = 1 if start_idx < end_idx else -1
            for i in range(start_idx, end_idx + step, step):
                rows[i].set_selected(True)
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            row.set_selected(not row.is_selected())
            
        self.last_clicked_row = row
        self.update_batch_toolbar()
    
    def load_events(self):
        self.combo_event.clear()
        events = self.controller.get_tombola_events(self.server_id)
        
        if not events:
            self.combo_event.addItem("(Sin jornadas)", None)
            return
        
        for event in events:
            self.combo_event.addItem(event.name, event.id)
        
        # Auto-select first event
        if self.combo_event.count() > 0 and self.combo_event.itemData(0) is not None:
            self.selected_event_id = self.combo_event.itemData(0)
            self.load_stores()
    
    def on_event_changed(self, index):
        event_id = self.combo_event.itemData(index)
        if event_id:
            self.selected_event_id = event_id
            self.load_stores()
        else:
            self.clear_stores()
    
    def load_stores(self):
        if not self.selected_event_id:
            return
        
        # Get data
        self.stores_data = self.controller.get_tombola_dashboard_data(self.server_id, self.selected_event_id)
        
        # Clear list
        self.store_list.clear()
        self.clear_details()
        
        if not self.stores_data:
            no_data = QListWidgetItem("(Sin cuentas)")
            no_data.setFlags(no_data.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.store_list.addItem(no_data)
            return
        
        # Populate list
        for store_data in self.stores_data:
            store_email = store_data['store'].email
            item = QListWidgetItem(f"📧 {store_email}")
            item.setData(Qt.ItemDataRole.UserRole, store_data)
            self.store_list.addItem(item)
        
        # Auto-select first
        if self.store_list.count() > 0:
            self.store_list.setCurrentRow(0)
            self.on_store_selected(self.store_list.item(0))
    
    def on_store_selected(self, item):
        selected_store_data = item.data(Qt.ItemDataRole.UserRole)
        if not selected_store_data:
            return
        
        self.clear_details()
        
        self.clear_details()
        
        self.current_details_widget = StoreDetailsWidget(
            selected_store_data, self.controller, self.selected_event_id, self
        )
        self.details_layout.addWidget(self.current_details_widget)
        
        for row in self.current_details_widget.rows:
            row.selectionChanged.connect(self.update_batch_toolbar)
            
        self.update_batch_toolbar()

    def update_batch_toolbar(self):
        if not self.current_details_widget:
            self.batch_toolbar.setVisible(False)
            return
        selected_count = sum(1 for row in self.current_details_widget.rows if row.is_selected())
        self.lbl_batch_count.setText(f"{selected_count} seleccionadas")
        self.batch_toolbar.setVisible(selected_count > 0)
    
    def clear_stores(self):
        self.store_list.clear()
        self.clear_details()
    
    def clear_details(self):
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def create_new_event(self):
        name, ok = QInputDialog.getText(
            self, 
            "Nueva Jornada de Tómbola", 
            "Nombre de la jornada (ej: Enero 2026, Evento Especial):"
        )
        
        if ok and name.strip():
            event = self.controller.create_tombola_event(self.server_id, name.strip())
            if event:
                QMessageBox.information(
                    self, 
                    "Jornada Creada", 
                    f"Jornada '{name}' creada exitosamente."
                )
                self.load_events()
            else:
                QMessageBox.warning(self, "Error", "No se pudo crear la jornada.")

    def on_import_requested(self):
        from PyQt6.QtWidgets import QFileDialog
        from app.utils.excel_importer import parse_account_file
        from app.controllers.alchemy_controller import AlchemyController
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Cuentas", "", "Excel/CSV Files (*.xlsx *.csv)"
        )
        
        if not file_path:
            return
            
        try:
            import_data = parse_account_file(file_path)
            # Use AlchemyController for importing since it has the generic method
            # In a real refactor, this could be shared in a BaseController
            controller = AlchemyController()
            success, message = controller.bulk_import_accounts(self.server_id, import_data)
            
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.load_stores() # Refresh list
            else:
                QMessageBox.warning(self, "Error de Importación", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error crítico al importar: {str(e)}")

    def show_help(self):
        from app.views.dialogs.help_shortcuts_dialog import HelpShortcutsDialog
        dialog = HelpShortcutsDialog(self)
        dialog.exec()
