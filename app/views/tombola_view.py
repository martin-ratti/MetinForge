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
        # Metin2 Palette: Compact
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: none;
                border-bottom: 1px solid #333;
                margin: 0px;
            }
            QCheckBox { spacing: 5px; }
            QCheckBox::indicator { width: 14px; height: 14px; }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2) 
        layout.setSpacing(5)
        self.setLayout(layout)

        # 0. Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)

        # Sort characters by ID to ensure consistency (Fixes "PJ" issue)
        chars = sorted(game_account.characters, key=lambda x: x.id)
        first_char = chars[0] if chars else None

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
        lbl_account.setFixedWidth(130) # Compact Std
        lbl_account.setStyleSheet("border: none; color: #e0e0e0; font-weight: bold; font-size: 12px;")
        
        # 2. Character Name (NO SLOTS)
        char_name = first_char.name if first_char else "-"
        display_name = char_name.split('_')[0] if '_' in char_name else char_name
        
        lbl_char = QLabel(display_name)
        lbl_char.setFixedWidth(130) # Compact Std
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
                    border: none;
                    border-bottom: 1px solid #333;
                    margin: 0px;
                }
            """)



class TombolaView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = TombolaController()
        
        self.stores_data = [] # List of {'store': store_obj, 'accounts': [game_account_objs]}
        self.all_stores_data = [] # Full dataset for filtering
        self.selected_event_id = None
        self.rows = [] # Track rows for valid selection scope
        self.last_clicked_row = None
        
        self.init_ui()
        self.setup_shortcuts()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT PANEL: Dashboard & Controls ---
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)
        
        # Header Left (Back Button + Title)
        header_left = QHBoxLayout()
        header_left.setSpacing(10)
        
        btn_back = QPushButton("← Volver")
        btn_back.setFixedWidth(100)
        btn_back.setFixedHeight(30)
        btn_back.clicked.connect(self.backRequested.emit)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #550000;
                border: 2px solid #800000;
                color: #ffcccc;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #800000;
            }
        """)
        
        left_title = QLabel(f"{self.server_name}")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d4af37;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        self.left_layout.addLayout(header_left)
        
        # Dashboard Widget
        from app.views.widgets.tombola_dashboard import TombolaDashboardWidget
        self.dashboard = TombolaDashboardWidget(self.controller)
        self.left_layout.addWidget(self.dashboard, 1) # Stretch to fill
        
        self.splitter.addWidget(self.left_widget)
        
        # --- RIGHT PANEL: All Accounts List ---
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)
        
        # Header Right Container
        self.header_right_widget = QWidget()
        header_right = QHBoxLayout()
        header_right.setContentsMargins(0, 0, 0, 0)
        header_right.setSpacing(10)
        self.header_right_widget.setLayout(header_right)
        
        lbl_server = QLabel(f"{self.server_name.upper()}")
        lbl_server.setStyleSheet("font-size: 20px; font-weight: bold; color: #eceff1;")
        header_right.addWidget(lbl_server)
        
        header_right.addStretch()
        
        # Store Filter
        self.combo_store = QComboBox()
        self.combo_store.setMinimumWidth(150)
        self.combo_store.setStyleSheet("padding: 5px; background-color: #263238; color: white; border: 1px solid #546e7a; border-radius: 4px;")
        self.combo_store.currentIndexChanged.connect(self.on_store_filter_changed)
        header_right.addWidget(self.combo_store)
        
        # Event Selector
        self.combo_event = QComboBox() 
        self.combo_event.setMinimumWidth(200)
        self.combo_event.setStyleSheet("padding: 5px; background-color: #37474f; color: white; border: 1px solid #546e7a; border-radius: 4px;")
        self.combo_event.currentIndexChanged.connect(self.on_event_changed)
        header_right.addWidget(self.combo_event)
        
        # New Event Button
        btn_add_event = QPushButton("➕ Nueva Jornada")
        btn_add_event.clicked.connect(self.create_new_event)
        btn_add_event.setStyleSheet("background-color: #f57f17; color: white; border-radius: 4px; font-weight: bold; padding: 5px 10px;")
        header_right.addWidget(btn_add_event)
        
        header_right.addSpacing(20)
        
        # Select All Button
        btn_select_all = QPushButton("Seleccionar Todo")
        btn_select_all.clicked.connect(self.select_all_rows)
        btn_select_all.setFixedHeight(30)
        btn_select_all.setStyleSheet("QPushButton { background-color: #455a64; color: white; border: 1px solid #607d8b; border-radius: 4px; font-weight: bold; padding: 0 10px; } QPushButton:hover { background-color: #546e7a; }")
        header_right.addWidget(btn_select_all)
        
        self.right_layout.addWidget(self.header_right_widget)
        
        # Scroll Area for Rows
        from app.utils.styles import SCROLLBAR_STYLESHEET
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }" + SCROLLBAR_STYLESHEET)
        
        self.content_container = QWidget()
        self.content_container.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_container.setLayout(self.content_layout)
        
        self.content_container.setLayout(self.content_layout)
        
        self.scroll.setWidget(self.content_container)
        self.right_layout.addWidget(self.scroll, 1)
        
        # Batch Toolbar (Bottom)
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
        
        self.right_layout.addWidget(self.batch_toolbar)
        
        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([300, 900])
        main_layout.addWidget(self.splitter)
        
        self.load_events()

    def setup_shortcuts(self):
        register_shortcuts(self, {
            'Ctrl+A': self.select_all_rows,
            'Ctrl+D': self.deselect_all_rows,
            '1': lambda: self.apply_batch_status(1),
            '2': lambda: self.apply_batch_status(-1),
            '3': lambda: self.apply_batch_status(0),
        })

    def select_all_rows(self):
        for row in self.rows:
            row.set_selected(True)

    def deselect_all_rows(self):
        for row in self.rows:
            row.set_selected(False)

    def apply_batch_status(self, status):
        selected_rows = [row for row in self.rows if row.is_selected()]
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
        print("DEBUG: Executing load_events")
        self.combo_event.blockSignals(True)
        self.combo_event.clear()
        
        events = self.controller.get_tombola_events(self.server_id)
        
        if not events:
            self.combo_event.addItem("(Sin jornadas)", None)
            self.combo_event.blockSignals(False)
            return
        
        for event in events:
            self.combo_event.addItem(event.name, event.id)
            
        # Select first event by default if available
        if self.combo_event.count() > 0:
            self.combo_event.setCurrentIndex(0)
            
        self.combo_event.blockSignals(False)
        # Manually trigger change for the initial selection
        self.on_event_changed(self.combo_event.currentIndex())
            
    def on_event_changed(self, index):
        if index < 0: return
        
        event_id = self.combo_event.itemData(index)
        self.selected_event_id = event_id
        if event_id:
            self.dashboard.set_event_id(event_id)
            self.load_stores()
        else:
            self.dashboard.set_event_id(None)
            self.clear_content()

    def on_store_filter_changed(self, index):
        self.filter_rows()
    
    def load_stores(self):
        if not self.selected_event_id: return
        
        # Get data
        self.all_stores_data = self.controller.get_tombola_dashboard_data(self.server_id, self.selected_event_id)
        
        # Populate Store Filter
        self.combo_store.blockSignals(True)
        self.combo_store.clear()
        self.combo_store.addItem("Todos", None)
        
        if self.all_stores_data:
            # Sort stores by email for the dropdown
            sorted_stores = sorted(self.all_stores_data, key=lambda x: x['store'].email)
            for item in sorted_stores:
                store = item['store']
                self.combo_store.addItem(store.email, store.id)
                
        self.combo_store.blockSignals(False)
        
        # Render initial view
        self.filter_rows()

    def filter_rows(self):
        self.clear_content()
        self.rows = []
        
        target_store_id = self.combo_store.currentData()
        
        # Filter data
        filtered_data = []
        if target_store_id is None:
            filtered_data = self.all_stores_data
        else:
            filtered_data = [s for s in self.all_stores_data if s['store'].id == target_store_id]
            
        if not filtered_data:
            lbl = QLabel("No hay cuentas para mostrar.")
            lbl.setStyleSheet("color: #a0a0a0; font-size: 14px; padding: 20px;")
            self.content_layout.addWidget(lbl)
            self.update_batch_toolbar()
            return

        # Header Definition
        header_container = QWidget()
        header_container.setStyleSheet("background-color: #263238; border-bottom: 2px solid #546e7a;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.setSpacing(5)
        header_container.setLayout(header_layout)
        
        # Checkbox Placeholder
        lbl_chk = QLabel("")
        lbl_chk.setFixedWidth(24)
        header_layout.addWidget(lbl_chk)

        lbl_h1 = QLabel("CUENTA")
        lbl_h1.setFixedWidth(130)
        lbl_h1.setStyleSheet("color: #eceff1; font-size: 11px; font-weight: bold;")
        
        lbl_h3 = QLabel("PERSONAJE")
        lbl_h3.setFixedWidth(130)
        lbl_h3.setStyleSheet("color: #eceff1; font-size: 11px; font-weight: bold;")
        
        header_layout.addWidget(lbl_h1)
        header_layout.addWidget(lbl_h3)
        
        from app.views.widgets.daily_grid import DailyGridHeaderWidget
        header_grid = DailyGridHeaderWidget(total_days=31)
        header_layout.addWidget(header_grid, 1)
        
        self.content_layout.addWidget(header_container)
        
        # Render rows
        for store_data in filtered_data:
            accounts = store_data.get('accounts', [])
            for game_account in accounts:
                row_widget = TombolaRow(game_account, self.controller, self.selected_event_id)
                row_widget.rowClicked.connect(self.on_row_clicked)
                row_widget.selectionChanged.connect(self.update_batch_toolbar)
                self.rows.append(row_widget)
                self.content_layout.addWidget(row_widget)
        
        self.update_batch_toolbar()

    def update_batch_toolbar(self):
        selected_count = sum(1 for row in self.rows if row.is_selected())
        self.lbl_batch_count.setText(f"{selected_count} seleccionadas")
        self.batch_toolbar.setVisible(selected_count > 0)
    
    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.rows = []
        self.last_clicked_row = None

    def on_row_clicked(self, row, modifiers):
        if row not in self.rows: return
        
        idx = self.rows.index(row)
        
        if modifiers & Qt.KeyboardModifier.ShiftModifier and self.last_clicked_row in self.rows:
            start = self.rows.index(self.last_clicked_row)
            end = idx
            step = 1 if start < end else -1
            for i in range(start, end + step, step):
                self.rows[i].set_selected(True)
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            row.set_selected(not row.is_selected())
             
        self.last_clicked_row = row
        self.update_batch_toolbar()
    
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
                # Select the new event
                idx = self.combo_event.findData(event.id)
                if idx >= 0: self.combo_event.setCurrentIndex(idx)
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
            controller = AlchemyController()
            success, message = controller.bulk_import_accounts(self.server_id, import_data)
            
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.load_stores() # Refresh list
            else:
                QMessageBox.warning(self, "Error de Importación", message)
        except Exception as e:
            QMessageBox.critical(self, "Error Crítico", f"Ocurrió un error al importar:\n{str(e)}")

    def show_help(self):
        from app.views.dialogs.help_shortcuts_dialog import HelpShortcutsDialog
        dialog = HelpShortcutsDialog(self)
        dialog.exec()
