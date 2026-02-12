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
        
        self.events_cache = []
        self.current_event = None
        self.all_data = [] 
        
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
        
        # --- QTREEVIEW ---
        self.tree_view = QTreeView()
        self.tree_view.setAlternatingRowColors(False)
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
                height: 24px;
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
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree_view.setExpandsOnDoubleClick(True)
        self.tree_view.setRootIsDecorated(True) 
        self.tree_view.installEventFilter(self) 
        
        self.tree_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | 
                                       QAbstractItemView.EditTrigger.EditKeyPressed | 
                                       QAbstractItemView.EditTrigger.AnyKeyPressed |
                                       QAbstractItemView.EditTrigger.SelectedClicked) 
        
        self.model = AlchemyModel([], event_id=None, controller=self.controller)
        self.tree_view.setModel(self.model)
        self.model.dataChanged.connect(self.on_model_data_changed)
        
        # Delegates
        self.grid_delegate = DailyGridDelegate(self.tree_view, total_days=30, controller=self.controller, model=self.model)
        self.store_header_delegate = StoreHeaderDelegate(self.tree_view)
        self.cords_delegate = CordsDelegate(self.tree_view)
        
        self.tree_view.setItemDelegateForColumn(3, self.grid_delegate)
        self.tree_view.setItemDelegateForColumn(4, self.cords_delegate)
        self.tree_view.setItemDelegate(self.store_header_delegate)
        
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
        
        try: self.tree_view.clicked.disconnect(self.on_tree_clicked)
        except: pass
        self.tree_view.clicked.connect(self.on_tree_clicked)

    def eventFilter(self, source, event):
        if source == self.tree_view and event.type() == QEvent.Type.KeyPress:
             key = event.text()
             
             # No interceptar teclas si estamos editando Cords (Columna 4)
             current_idx = self.tree_view.currentIndex()
             if current_idx.isValid() and current_idx.column() == 4:
                 return super().eventFilter(source, event)

             if key in ['1', '2', '3']:
                 status_map = {'1': 1, '2': -1, '3': 0}
                 if key in status_map:
                     self.handle_burst_action(status_map[key])
                     return True
        
        return super().eventFilter(source, event)

    def on_tree_clicked(self, index):
        """Seleccionar grupo Store al hacer clic en un header."""
        if not index.isValid(): return
        
        if index.data(AlchemyModel.TypeRole) == "store":
            self.tree_view.selectionModel().clearSelection()
            
            model = self.model
            rows = model.rowCount(index)
            if rows > 0:
                selection = self.tree_view.selectionModel()
                for r in range(rows):
                    child_idx = model.index(r, 0, index)
                    selection.select(child_idx, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)

    def select_all(self):
        self.tree_view.selectAll()
        
    def deselect_all(self):
        self.tree_view.clearSelection()

    def handle_burst_action(self, status):
        """Modo Rafaga: Aplica el estado a TODAS las filas seleccionadas."""
        selected_indexes = self.tree_view.selectionModel().selectedRows()
        
        if not selected_indexes:
            idx = self.tree_view.currentIndex()
            if idx.isValid(): selected_indexes = [idx]
            else: return

        account_indexes = [ix for ix in selected_indexes if ix.data(AlchemyModel.TypeRole) == "account"]
        
        if not account_indexes:
            self.move_selection_next()
            return

        for index in account_indexes:
            account = index.data(AlchemyModel.RawDataRole)
            char = account.characters[0] if account.characters else None
            
            if char and self.current_event:
                day_to_update = 1
                if status == 0:
                     day_to_update = self.controller.get_next_pending_day(char.id, self.current_event.id)
                     day_to_update = max(1, day_to_update - 1)
                else:
                     day_to_update = self.controller.get_next_pending_day(char.id, self.current_event.id)
                
                if day_to_update > 1:
                    activity = getattr(account, 'current_event_activity', {})
                    prev_status = activity.get(day_to_update - 1, 0)
                    if prev_status == 0:
                        continue
                
                self.controller.update_daily_status(char.id, day_to_update, status, self.current_event.id)
                self.model.update_daily_status(index, day_to_update, status)
        
        if len(account_indexes) == 1:
             self.move_selection_next()
            
    def on_model_data_changed(self, top_left, bottom_right, roles):
        """Refrescar contadores cuando cambian datos."""
        if AlchemyModel.CordsRole in roles or AlchemyModel.GridDataRole in roles or Qt.ItemDataRole.EditRole in roles:
             if self.alchemy_counters_widget and self.current_event:
                 self.alchemy_counters_widget.update_counts()
                 total = self.model.get_total_event_cords()
                 self.alchemy_counters_widget.set_total_cords(total)

    def move_selection_next(self):
        """Mueve la seleccion a la siguiente fila visible, saltando Stores."""
        current_idx = self.tree_view.currentIndex()
        next_idx = self.tree_view.indexBelow(current_idx)
        
        if next_idx.isValid():
            self.tree_view.setCurrentIndex(next_idx)
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
        if self.alchemy_counters_widget:
            self.alchemy_counters_widget.set_event(self.current_event.id if self.current_event else None)
        self.load_data()

    def prompt_add_email(self):
        email, ok = QInputDialog.getText(self, "Agregar Correo", "Correo electrónico:")
        if ok and email:
             self.controller.create_store(email, self.server_id)
             self.load_data()

    def on_import_requested(self):
         from PyQt6.QtWidgets import QFileDialog
         from app.utils.excel_importer import parse_account_file
         file_path, _ = QFileDialog.getOpenFileName(self, "Importar", "", "Excel (*.xlsx);;CSV (*.csv)")
         if file_path:
             try:
                 data = parse_account_file(file_path)
                 logger.info(f"Importando archivo: {file_path}")
                 
                 if isinstance(data, dict):
                     logger.info(f"  Email detectado: {data.get('email', 'N/A')}")
                     logger.info(f"  Personajes encontrados: {len(data.get('characters', []))}")
                     if not data.get('email') or not data.get('characters'):
                         QMessageBox.warning(self, "Importacion", "No se encontraron datos validos en el archivo.\nVerifica que el formato sea correcto.")
                         return
                 elif isinstance(data, list):
                     if not data:
                         QMessageBox.warning(self, "Importacion", "No se encontraron datos validos en el archivo.\nVerifica que el formato sea correcto.")
                         return
                     logger.info(f"  Grupos encontrados: {len(data)}")
                 else:
                     QMessageBox.warning(self, "Importacion", "Formato de datos no reconocido.")
                     return
                 
                 ok, msg = self.controller.bulk_import_accounts(self.server_id, data)
                 if ok:
                     QMessageBox.information(self, "Importacion Exitosa", msg)
                 else:
                     QMessageBox.warning(self, "Error en Importacion", msg)
                 self.load_data()
             except Exception as e:
                 logger.error(f"Error al importar archivo: {e}")
                 QMessageBox.critical(self, "Error", f"Error al procesar el archivo:\n{e}")

    def load_data(self):
        if not self.current_event:
            self.model.set_data([], None)
            return

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
        
        if current_store_id:
             idx = self.combo_store.findData(current_store_id)
             if idx >= 0: self.combo_store.setCurrentIndex(idx)
             
        self.combo_store.blockSignals(False)
        self.apply_filter_and_set_model()

    def on_store_filter_changed(self, index):
        self.apply_filter_and_set_model()

    def apply_filter_and_set_model(self):
        target_store_id = self.combo_store.currentData()
        if target_store_id is None:
            filtered_data = self.all_data
        else:
            filtered_data = [s for s in self.all_data if s['store'].id == target_store_id]
            
        cords_summary = self.controller.get_all_daily_cords(self.current_event.id) if self.current_event else {}
        
        # Calcular dia actual relativo al evento
        current_day = 1
        if self.current_event:
             today = datetime.date.today()
             start = self.current_event.created_at
             if isinstance(start, str):
                  try: start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
                  except: start = today
             
             delta = (today - start).days + 1
             current_day = max(1, min(delta, self.current_event.total_days))

        self.model._current_day = current_day
        self.model.set_data(filtered_data, self.current_event.id if self.current_event else None, cords_summary)
        
        self.grid_delegate.total_days = self.current_event.total_days if self.current_event else 0
        
        if self.alchemy_counters_widget and self.current_event:
             self.alchemy_counters_widget.set_total_cords(self.model.get_total_event_cords())
        
        self.tree_view.expandAll()
        
        # Span para Store Headers
        for row in range(self.model.rowCount()):
             self.tree_view.setFirstColumnSpanned(row, QModelIndex(), True) 

        if self.current_event:
             self.grid_delegate.total_days = self.current_event.total_days
             
        # Configurar columnas
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 40)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 50)
        header.setStretchLastSection(False)
