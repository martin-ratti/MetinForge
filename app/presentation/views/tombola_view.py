from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeView, 
                             QSplitter, QPushButton, QInputDialog, QMessageBox, QComboBox,
                             QHeaderView, QAbstractItemView, QApplication)
from PyQt6.QtGui import QAction, QStandardItemModel, QStandardItem, QIcon, QCursor
from PyQt6.QtCore import Qt, QModelIndex, QEvent, QTimer, pyqtSignal, QItemSelectionModel
from app.utils.logger import logger
from app.application.services.tombola_service import TombolaService
from app.presentation.models.tombola_model import TombolaModel
from app.presentation.delegates.tombola_grid_delegate import TombolaGridDelegate
from app.utils.feedback import FeedbackManager
from app.utils.shortcuts import register_shortcuts
from app.presentation.styles import AppStyles
import datetime

class TombolaView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name, controller=None):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = controller if controller else TombolaService()
        self.feedback = FeedbackManager.instance()
        
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
        
        # Panel izquierdo
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        header_left = QHBoxLayout()
        header_left.setSpacing(10)
        
        btn_back = QPushButton("← Volver")
        btn_back.setFixedWidth(100)
        btn_back.setFixedHeight(30)
        btn_back.clicked.connect(self.backRequested.emit)
        btn_back.setStyleSheet(AppStyles.BUTTON_BACK)
        
        left_title = QLabel(f"{self.server_name}")
        left_title.setStyleSheet(AppStyles.LABEL_TITLE)
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        left_layout.addLayout(header_left)
        
        from app.presentation.views.widgets.tombola_dashboard import TombolaDashboardWidget
        self.dashboard = TombolaDashboardWidget(self.controller)
        left_layout.addWidget(self.dashboard, 1)
        
        # Panel derecho (TreeView)
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_widget.setLayout(right_layout)
        
        header_right = QHBoxLayout()
        header_right.setSpacing(10)
        
        lbl_server = QLabel(f"{self.server_name.title()}")
        lbl_server.setStyleSheet(AppStyles.LABEL_BADGE)
        header_right.addWidget(lbl_server)
        header_right.addStretch()
        
        self.combo_store = QComboBox()
        self.combo_store.setMinimumWidth(150)
        self.combo_store.setStyleSheet(AppStyles.COMBO_BOX)
        self.combo_store.currentIndexChanged.connect(self.on_store_filter_changed)
        header_right.addWidget(self.combo_store)
        
        self.combo_events = QComboBox()
        self.combo_events.setMinimumWidth(200)
        self.combo_events.setStyleSheet(AppStyles.COMBO_BOX)
        self.combo_events.currentIndexChanged.connect(self.on_event_changed)
        header_right.addWidget(self.combo_events)
        
        self.btn_new_event = QPushButton("Nueva Jornada")
        self.btn_new_event.clicked.connect(self.prompt_create_event)
        self.btn_new_event.setStyleSheet(AppStyles.BUTTON_ACCENT)
        header_right.addWidget(self.btn_new_event)
        
        right_layout.addLayout(header_right)
        
        # TreeView
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
        
        self.model = TombolaModel([], event_id=None, controller=self.controller)
        self.tree_view.setModel(self.model)
        
        self.grid_delegate = TombolaGridDelegate(self.tree_view, controller=self.controller, model=self.model)
        self.tree_view.setItemDelegateForColumn(2, self.grid_delegate)
        
        try: self.tree_view.clicked.disconnect(self.on_tree_clicked)
        except: pass
        self.tree_view.clicked.connect(self.on_tree_clicked)

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

    def eventFilter(self, source, event):
        if source == self.tree_view and event.type() == QEvent.Type.KeyPress:
             key = event.text()
             if key in ['1', '2', '3']:
                 status_map = {'1': 1, '2': -1, '3': 0}
                 if key in status_map:
                     self.handle_burst_action(status_map[key])
                     return True
        return super().eventFilter(source, event)

    def on_tree_clicked(self, index):
        if not index.isValid(): return
        if index.data(TombolaModel.TypeRole) == "store":
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
        """Modo Burst: 1=OK, -1=Fail, 0=Reset/Undo."""
        selected_indexes = self.tree_view.selectionModel().selectedRows()
        
        if not selected_indexes:
            idx = self.tree_view.currentIndex()
            if idx.isValid(): selected_indexes = [idx]
            else: return

        account_indexes = [ix for ix in selected_indexes if ix.data(TombolaModel.TypeRole) == "account"]
        
        if not account_indexes:
            self.move_selection_next()
            return

        if status == 1: self.feedback.play_success()
        elif status == -1: self.feedback.play_fail()

        for index in account_indexes:
            account = index.data(TombolaModel.RawDataRole)
            char = account.characters[0] if account.characters else None
            
            if char and self.current_event:
                day_to_update = 1
                if status == 0:
                     last_day = self.controller.get_last_filled_day(char.id, self.current_event.id)
                     day_to_update = last_day if last_day and last_day > 0 else 1
                else:
                     day_to_update = self.controller.get_next_pending_day(char.id, self.current_event.id)
                
                self.controller.update_daily_status(char.id, day_to_update, status, self.current_event.id)
                self.model.update_daily_status(index, day_to_update, status)

        if self.dashboard and self.current_event:
             self.dashboard.update_stats()

        if len(account_indexes) == 1:
             self.move_selection_next()

    def move_selection_next(self):
        current_idx = self.tree_view.currentIndex()
        next_idx = self.tree_view.indexBelow(current_idx)
        
        if next_idx.isValid():
            self.tree_view.setCurrentIndex(next_idx)
            if next_idx.data(TombolaModel.TypeRole) == "store":
                 self.move_selection_next()

    def load_events(self):
        self.events_cache = self.controller.get_tombola_events(self.server_id)
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
            if self.dashboard:
                 self.dashboard.set_event_id(self.current_event.id)
            
        self.combo_events.blockSignals(False)
        self.load_data()

    def prompt_create_event(self):
        name, ok = QInputDialog.getText(self, "Nueva Jornada", "Nombre:")
        if ok and name:
            new_ev = self.controller.create_tombola_event(self.server_id, name)
            if new_ev: self.load_events()

    def on_event_changed(self, index):
        if index < 0: return
        self.current_event = self.combo_events.itemData(index)
        if self.dashboard:
             self.dashboard.set_event_id(self.current_event.id if self.current_event else None)
        self.load_data()

    def load_data(self):
        if not self.current_event:
            self.model.set_data([], None)
            return

        dto = self.controller.get_tombola_dashboard_data(self.server_id, self.current_event.id)
        self.all_data = dto.store_accounts
        
        self.combo_store.blockSignals(True)
        current_store_id = self.combo_store.currentData()
        self.combo_store.clear()
        self.combo_store.addItem("Todos", None)
        
        sorted_stores = sorted(self.all_data, key=lambda x: x.email)
        for store in sorted_stores:
             self.combo_store.addItem(store.email, store.id)
        
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
            filtered_data = [s for s in self.all_data if s.id == target_store_id]
            
        self.model.set_data(filtered_data, self.current_event.id if self.current_event else None)
        self.tree_view.expandAll()
        
        for row in range(self.model.rowCount()):
             self.tree_view.setFirstColumnSpanned(row, QModelIndex(), True)

        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
