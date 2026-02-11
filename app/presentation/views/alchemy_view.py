from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeView, 
                             QSplitter, QPushButton, QInputDialog, QMessageBox, QComboBox,
                             QHeaderView, QAbstractItemView, QApplication, QAbstractSpinBox, QLineEdit)
from PyQt6.QtGui import QAction, QStandardItemModel, QStandardItem, QIcon, QCursor
from PyQt6.QtCore import Qt, QModelIndex, QEvent, QTimer, pyqtSignal, QItemSelectionModel
from app.utils.logger import logger
from app.application.services.alchemy_service import AlchemyService
from app.presentation.models.alchemy_model import AlchemyModel
from app.presentation.delegates.daily_grid_delegate import DailyGridDelegate
from app.presentation.delegates.store_header_delegate import StoreHeaderDelegate
from app.presentation.delegates.cords_delegate import CordsDelegate
from app.presentation.views.widgets.alchemy_counters_widget import AlchemyCountersWidget
from app.utils.shortcuts import register_shortcuts
import datetime

class AlchemyView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = AlchemyService()
        
        # Data & State
        self.events_cache = []
        self.current_event = None
        self.all_data = [] 
        
        # UI Components
        self.tree_view = None
        self.model = None
        
        self.init_ui()
        self.setup_shortcuts()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT PANEL ---
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Header Left
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
            QPushButton:hover { background-color: #800000; }
        """)
        
        left_title = QLabel(f"{self.server_name}")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d4af37;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        left_layout.addLayout(header_left)
        
        # Toolbar
        btn_add_email = QPushButton("📧+ Correo") 
        btn_add_email.clicked.connect(self.prompt_add_email)
        btn_add_email.setStyleSheet("QPushButton { background-color: #1565c0; color: white; border: 1px solid #1e88e5; border-radius: 4px; font-weight: bold; }")
        
        btn_import = QPushButton("📥 Importar")
        btn_import.clicked.connect(self.on_import_requested)
        btn_import.setStyleSheet("QPushButton { background-color: #455a64; color: white; border: 1px solid #607d8b; border-radius: 4px; font-weight: bold; }")
        
        email_toolbar = QHBoxLayout()
        email_toolbar.addWidget(btn_add_email)
        email_toolbar.addWidget(btn_import)
        left_layout.addLayout(email_toolbar)
        
        # Counters Widget
        self.alchemy_counters_widget = AlchemyCountersWidget(
            controller=self.controller,
            event_id=None
        )
        left_layout.addWidget(self.alchemy_counters_widget)
        
        # --- RIGHT PANEL (TREE VIEW) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_widget.setLayout(right_layout)
        
        # Header Right
        header_right = QHBoxLayout()
        header_right.setSpacing(10)
        
        lbl_server = QLabel(f"{self.server_name.title()}")
        lbl_server.setStyleSheet("font-size: 14px; font-weight: bold; color: #d4af37; background-color: #263238; border: 1px solid #d4af37; border-radius: 4px; padding: 4px 8px;")
        header_right.addWidget(lbl_server)
        header_right.addStretch()
        
        # Filters
        self.combo_store = QComboBox()
        self.combo_store.setMinimumWidth(150)
        self.combo_store.setStyleSheet("padding: 5px; background-color: #263238; color: white; border: 1px solid #546e7a; border-radius: 4px;")
        self.combo_store.currentIndexChanged.connect(self.on_store_filter_changed)
        header_right.addWidget(self.combo_store)
        
        self.combo_events = QComboBox()
        self.combo_events.setMinimumWidth(200)
        self.combo_events.setStyleSheet("padding: 5px; background-color: #37474f; color: white; border: 1px solid #546e7a; border-radius: 4px;")
        self.combo_events.currentIndexChanged.connect(self.on_event_changed)
        header_right.addWidget(self.combo_events)
        
        self.btn_new_event = QPushButton("➕ Nueva Jornada")
        self.btn_new_event.clicked.connect(self.prompt_create_event)
        self.btn_new_event.setStyleSheet("background-color: #f57f17; color: white; border-radius: 4px; font-weight: bold; padding: 5px 10px;")
        header_right.addWidget(self.btn_new_event)
        
        right_layout.addLayout(header_right)
        
        # --- QTREEVIEW IMPLEMENTATION ---
        self.tree_view = QTreeView()
        self.tree_view.setAlternatingRowColors(False) # Manejado por estilo
        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: #1a1a1a;
                border: none;
                color: #e0e0e0;
                font-size: 13px;
                outline: none;
            }
            QTreeView::item {
                border-bottom: 1px solid #333;
                padding: 0px;
                height: 24px; /* Altura Fija Compacta */
            }
            QTreeView::item:selected {
                background-color: #2d2d1b;
                border: 1px solid #d4af37;
            }
            QHeaderView::section {
                background-color: #263238;
                color: #eceff1;
                padding: 4px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # Allow multiple row selection (Ctrl+A support)
        self.tree_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree_view.setExpandsOnDoubleClick(True)
        self.tree_view.setRootIsDecorated(False) # Ocultar flecha de expansión si queremos flat look, pero es árbol
        # User wants "Yellow Row" separator. We can use setRootIsDecorated(True) to allow collapse store.
        # User wants "Yellow Row" separator. We can use setRootIsDecorated(True) to allow collapse store.
        self.tree_view.setRootIsDecorated(True) 
        self.tree_view.installEventFilter(self) 
        
        # Single Click Edit for Cords (Column 4)
        # EditTriggers: DoubleClicked | EditKeyPressed | AnyKeyPressed
        # To verify: Standard is DoubleClicked. User wants "One click".
        # We can add SelectedClicked or CurrentChanged? 
        # But that might trigger edit for other columns too? No, only editable ones.
        # Only Col 4 is editable in our model.
        self.tree_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | 
                                       QAbstractItemView.EditTrigger.EditKeyPressed | 
                                       QAbstractItemView.EditTrigger.AnyKeyPressed |
                                       QAbstractItemView.EditTrigger.SelectedClicked) 
        
        # Init Model
        self.model = AlchemyModel([], event_id=None, controller=self.controller)
        self.tree_view.setModel(self.model)
        
        # Connect signals for Global Counter Update
        self.model.dataChanged.connect(self.on_model_data_changed)
        
        # Init Delegates
        self.grid_delegate = DailyGridDelegate(self.tree_view, total_days=30, controller=self.controller, model=self.model)
        self.store_header_delegate = StoreHeaderDelegate(self.tree_view)
        self.cords_delegate = CordsDelegate(self.tree_view)
        
        self.tree_view.setItemDelegateForColumn(3, self.grid_delegate)
        self.tree_view.setItemDelegateForColumn(4, self.cords_delegate)
        self.tree_view.setItemDelegate(self.store_header_delegate) # Sets globally, specific columns override? No, row based.
        # Wait, QStyledItemDelegate applies to all. We need logic inside paint() to distinguish type.
        # AlchemyModel.TypeRole helps.
        # Actually, "setItemDelegate" sets it for ALL items. 
        # But we want specific behavior for column 3 (Grid) vs others vs Store Headers.
        # QTreeView supports setItemDelegate (global) and setItemDelegateForColumn.
        # If we set global, column delegate takes precedence? Yes usually.
        # Let's verify: Global Delegate will handle "Store Rows" (crossing columns via paint).
        # And Column 3 Delegate will handle Grid for "Accounts".
        
        # PROBLEM: Store Header spans multiple columns. 
        # By default TreeView draws separate cells.
        # To make Store Header look like one big bar, we use setFirstColumnSpanned 
        # inside the view logic when loading data.
        
        right_layout.addWidget(self.tree_view)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)
        
        self.load_events()

    def setup_shortcuts(self):
        register_shortcuts(self, {
            'Ctrl+A': self.select_all,
            'Ctrl+D': self.deselect_all,
        })
        
        # Conectar señal de clic para detectar clic en Store Header
        # Desconectar primero por seguridad si se llama múltiples veces (aunque setup_shortcuts es solo init)
        try: self.tree_view.clicked.disconnect(self.on_tree_clicked)
        except: pass
        self.tree_view.clicked.connect(self.on_tree_clicked)

    def eventFilter(self, source, event):
        if source == self.tree_view and event.type() == QEvent.Type.KeyPress:
             # Check for Input Mode (Editor Open)
             # If an editor is open, it usually has focus, not the tree view.
             # But QTreeView might have focus while delegate editor is active?
             # No, editor widget takes focus.
             
             key = event.text()
             
             # Disable shortcuts if editing Cords Column (4)
             current_idx = self.tree_view.currentIndex()
             if current_idx.isValid() and current_idx.column() == 4:
                 return super().eventFilter(source, event)

             if key in ['1', '2', '3']:
                 # Check modifiers?
                 # If user is typing in a search box... TreeView search?
                 # We want to override TreeView default search with our Burst Action.
                 
                 status_map = {'1': 1, '2': -1, '3': 0}
                 if key in status_map:
                     self.handle_burst_action(status_map[key])
                     return True # Consume event
        
        return super().eventFilter(source, event)

    def on_tree_clicked(self, index):
        """Manejar clic para seleccionar grupo Store"""
        if not index.isValid(): return
        
        if index.data(AlchemyModel.TypeRole) == "store":
            # Select all child accounts
            # Store item has no children in the View sense because it's a Tree? 
            # Yes, standard tree.
            # Select all children of this index.
            self.tree_view.selectionModel().clearSelection()
            
            # Create a selection range covering all children
            model = self.model
            rows = model.rowCount(index)
            if rows > 0:
                first_child = model.index(0, 0, index)
                last_child = model.index(rows - 1, model.columnCount(index) - 1, index)
                
                # Selection Range
                selection = self.tree_view.selectionModel()
                # Select rows
                # Loop through children to select rows safely
                for r in range(rows):
                    child_idx = model.index(r, 0, index)
                    selection.select(child_idx, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)

    def select_all(self):
        self.tree_view.selectAll()
        
    def deselect_all(self):
        self.tree_view.clearSelection()

    def handle_burst_action(self, status):
        """
        Modo Ráfaga (Batch Action Support):
        Itera sobre TODAS las filas seleccionadas y aplica el cambio secuencial.
        """
        selected_indexes = self.tree_view.selectionModel().selectedRows()
        
        if not selected_indexes:
            # Fallback to current index if no full row selected (unlikely with SelectRows)
            idx = self.tree_view.currentIndex()
            if idx.isValid(): selected_indexes = [idx]
            else: return

        # Filter: Only Account Rows
        account_indexes = [ix for ix in selected_indexes if ix.data(AlchemyModel.TypeRole) == "account"]
        
        if not account_indexes:
            self.move_selection_next()
            return

        # Optimization: Prepare batch update
        # If many rows, we should block signals or group updates?
        # Controller updates are individual DB transactions unless bulk method exists.
        # For now, loop. User said "50 cuentas...". 50 updates is fine.
        
        for index in account_indexes:
            account = index.data(AlchemyModel.RawDataRole)
            char = account.characters[0] if account.characters else None
            
            if char and self.current_event:
                # Calculate Day
                day_to_update = 1
                if status == 0:
                     day_to_update = self.controller.get_next_pending_day(char.id, self.current_event.id)
                     day_to_update = max(1, day_to_update - 1)
                else:
                     day_to_update = self.controller.get_next_pending_day(char.id, self.current_event.id)
                
                # Sequential Validation
                if day_to_update > 1:
                    activity = getattr(account, 'current_event_activity', {})
                    prev_status = activity.get(day_to_update - 1, 0)
                    if prev_status == 0:
                        continue # Skip this account if sequence broken
                
                # Update
                self.controller.update_daily_status(char.id, day_to_update, status, self.current_event.id)
                self.model.update_daily_status(index, day_to_update, status)
        
        # Move Selection (Only if single selection? Or keep selection?)
        # If user selected 50 rows, they probably want to keep them selected if they pressed '1'?
        # Or maybe they want to move to next 50?
        # Usually Batch Action applies to selection.
        # If checking multiple days (1, 1, 1...), typically we stay on selection and day increments.
        # But get_next_pending_day will increment automatically!
        # So repeated pressing of '1' on same selection will fill days 1, 2, 3...
        # THIS IS POWERFUL.
        
        # But if single row, functionality implies moving to next row.
        # Rule: If Single Selection -> Move Next. If Multi Selection -> Keep Selection (to allow filling days).
        if len(account_indexes) == 1:
             self.move_selection_next()
            
    def on_model_data_changed(self, top_left, bottom_right, roles):
        # Refresh counters if Cords changed
        # This catches updates from both Grid changes (indirectly affects totals?) and Cords edits.
        # Ideally we only update if relevant data changed.
        if AlchemyModel.CordsRole in roles or AlchemyModel.GridDataRole in roles or Qt.ItemDataRole.EditRole in roles:
             if self.alchemy_counters_widget and self.current_event:
                 # Update counters (Alchemy Types still from DB)
                 self.alchemy_counters_widget.update_counts()
                 # Override Total Cords with Memory Calculation (Instant Update)
                 total = self.model.get_total_event_cords()
                 self.alchemy_counters_widget.set_total_cords(total)

    def move_selection_next(self):
        """Mueve la selección a la siguiente fila visible, saltando Stores si es necesario"""
        current_idx = self.tree_view.currentIndex()
        next_idx = self.tree_view.indexBelow(current_idx)
        
        if next_idx.isValid():
            self.tree_view.setCurrentIndex(next_idx)
            # Si caímos en un Store, avanzar uno más
            if next_idx.data(AlchemyModel.TypeRole) == "store":
                 self.move_selection_next()

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
        self.load_data()

    # ... (Keep prompt_create_event, on_event_changed, etc logic similar to before) ...
    # Simplified imports for valid execution
    def prompt_create_event(self):
        from app.presentation.views.dialogs.event_dialog import EventDialog
        dialog = EventDialog(self)
        dialog.txt_name.setText(f"Evento {len(self.events_cache) + 1}")
        if dialog.exec():
            name, days = dialog.get_data()
            if name:
                new_ev = self.controller.create_alchemy_event(self.server_id, name, days)
                if new_ev: self.load_events()

    def on_event_changed(self, index):
        if index < 0: return
        self.current_event = self.combo_events.itemData(index)
        # Update Counter Widget
        if self.alchemy_counters_widget:
            self.alchemy_counters_widget.set_event(self.current_event.id if self.current_event else None)
        self.load_data()

    def prompt_add_email(self):
        # Implementation relying on existing logic or similar
        email, ok = QInputDialog.getText(self, "Agregar Correo", "Correo electrónico:")
        if ok and email:
             self.controller.create_store(email, self.server_id)
             self.load_data()

    def on_import_requested(self):
         from PyQt6.QtWidgets import QFileDialog
         from app.utils.excel_importer import parse_account_file
         file_path, _ = QFileDialog.getOpenFileName(self, "Importar", "", "Excel (*.xlsx);;CSV (*.csv)")
         if file_path:
             data = parse_account_file(file_path)
             self.controller.bulk_import_accounts(self.server_id, data)
             self.load_data()

    def load_data(self):
        if not self.current_event:
            self.model.set_data([], None)
            return

        # Get Data
        raw_data = self.controller.get_alchemy_dashboard_data(self.server_id, event_id=self.current_event.id)
        self.all_data = raw_data
        
        # Populate Filter
        self.combo_store.blockSignals(True)
        current_store_id = self.combo_store.currentData()
        self.combo_store.clear()
        self.combo_store.addItem("Todos", None)
        
        sorted_stores = sorted(self.all_data, key=lambda x: x['store'].email)
        for item in sorted_stores:
             self.combo_store.addItem(item['store'].email, item['store'].id)
        
        # Restore selection if possible
        if current_store_id:
             idx = self.combo_store.findData(current_store_id)
             if idx >= 0: self.combo_store.setCurrentIndex(idx)
             
        self.combo_store.blockSignals(False)
        
        self.apply_filter_and_set_model()

    def on_store_filter_changed(self, index):
        self.apply_filter_and_set_model()

    def apply_filter_and_set_model(self):
        target_store_id = self.combo_store.currentData()
        filtered_data = []
        if target_store_id is None:
            filtered_data = self.all_data
        else:
            filtered_data = [s for s in self.all_data if s['store'].id == target_store_id]
            
        # Get Cords Summary (Daily Records)
        cords_summary = self.controller.get_all_daily_cords(self.current_event.id) if self.current_event else {}
        
        # Calculate Current Day (Default logic)
        current_day = 1
        if self.current_event:
             # Basic logic: days since start? Or just 1 for now/last active?
             # In old view: current_day = self._calculate_current_day()
             # We should port that logic or default to today's index relative to start
             today = datetime.date.today()
             start = self.current_event.created_at # Assuming event has created_at date object
             if isinstance(start, str): # Safety check
                  try: start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
                  except: start = today
             
             delta = (today - start).days + 1
             current_day = max(1, min(delta, self.current_event.total_days))

        # Update Model
        self.model._current_day = current_day # Set explicitly
        self.model.set_data(filtered_data, self.current_event.id if self.current_event else None, cords_summary)
        
        # Update Dictionary in Delegate
        self.grid_delegate.total_days = self.current_event.total_days if self.current_event else 0
        
        # Force Widget Update from Model Data
        if self.alchemy_counters_widget and self.current_event:
             self.alchemy_counters_widget.set_total_cords(self.model.get_total_event_cords())
        
        self.tree_view.expandAll()
        
        # Apply Spans for Store Headers
        # We need to iterate model rows (Stores) and set span
        for row in range(self.model.rowCount()):
             # Span columns 0, 1, 2. Leave 3 for Grid Header, 4 for Cords total?
             # User wants day numbers above. Store row is perfect for this.
             # Span 0-2 (Account, Slots, PJ) -> "Email"
             # Grid column 3 -> "1 2 3 ... 30"
             # Cords column 4 -> "Total Cords"?
             self.tree_view.setFirstColumnSpanned(row, QModelIndex(), True) 
             # setFirstColumnSpanned ONLY spans the indentation area + first column.
             # It does NOT span across arbitrary columns 1, 2, 3.
             # To simulate a full row, we usually rely on the delegate painting over everything 
             # and the view ignoring column boundaries for that row? 
             # QTreeView doesn't support col-spanning easily.
             # BUT: The user liked the aesthetic. In my previous code, StoreHeaderDelegate painted everything.
             # If I want to put the Grid Header in Col 3, I need to prevent StoreHeaderDelegate from painting over Col 3.
             # AND I need col 3 to be visible.
             # Currently StoreHeaderDelegate paints rect. 
             pass

        # Update Delegate Total Days
        if self.current_event:
             self.grid_delegate.total_days = self.current_event.total_days
             
        # Configure Columns
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Cuenta
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed) # Slots
        header.resizeSection(1, 40)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # PJ
        
        # FIX Scroll: Stretch compresses content. ResizeToContents forces full width => ScrollBar appears
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed) # Cords
        header.resizeSection(4, 50)
        
        header.setStretchLastSection(False) # Important for horizontal scroll
