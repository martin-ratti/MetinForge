from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeView, 
                             QSplitter, QPushButton, QComboBox, QHeaderView, QAbstractItemView, QMessageBox, QInputDialog)
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtCore import Qt, QModelIndex, QEvent, pyqtSignal, QItemSelectionModel
from app.application.services.fishing_service import FishingService
from app.presentation.models.fishing_model import FishingModel
from app.presentation.delegates.fishing_grid_delegate import FishingGridDelegate
from app.presentation.utils.feedback import FeedbackManager
from app.utils.shortcuts import register_shortcuts
from app.utils.logger import logger
import datetime

class FishingView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = FishingService()
        self.feedback = FeedbackManager.instance()
        self.current_year = datetime.date.today().year
        self.all_data = [] 
        
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
        
        left_title = QLabel("Pesca Anual")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d4af37;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        left_layout.addLayout(header_left)
        
        stats_layout = QVBoxLayout()
        
        btn_import = QPushButton("Importar Excel")
        btn_import.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1b5e20;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #388e3c; }
        """)
        btn_import.clicked.connect(self.import_excel)
        stats_layout.addWidget(btn_import)
        
        stats_layout.addStretch()
        left_layout.addLayout(stats_layout)
        
        # Panel derecho
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_widget.setLayout(right_layout)
        
        top_bar = QHBoxLayout()
        lbl_server = QLabel(f"{self.server_name.title()}")
        lbl_server.setStyleSheet("font-size: 14px; font-weight: bold; color: #d4af37; background-color: #263238; border: 1px solid #d4af37; border-radius: 4px; padding: 4px 8px;")
        
        self.combo_year = QComboBox()
        for y in range(2025, 2031):
            self.combo_year.addItem(str(y))
        self.combo_year.setCurrentText(str(self.current_year))
        self.combo_year.setStyleSheet("padding: 5px; background-color: #37474f; color: white;")
        self.combo_year.currentIndexChanged.connect(self.on_year_changed)
        
        self.combo_store = QComboBox()
        self.combo_store.setMinimumWidth(150)
        self.combo_store.setStyleSheet("padding: 5px; background-color: #37474f; color: white; border: 1px solid #546e7a; border-radius: 4px;")
        self.combo_store.currentIndexChanged.connect(self.on_store_filter_changed)
        
        top_bar.addWidget(lbl_server)
        top_bar.addStretch()
        top_bar.addWidget(self.combo_store)
        top_bar.addWidget(QLabel("Año:"))
        top_bar.addWidget(self.combo_year)
        
        right_layout.addLayout(top_bar)
        
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
                height: 46px;
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
        
        self.model = FishingModel([], year=self.current_year, controller=self.controller)
        self.tree_view.setModel(self.model)
        
        self.grid_delegate = FishingGridDelegate(self.tree_view, controller=self.controller, model=self.model)
        self.tree_view.setItemDelegateForColumn(2, self.grid_delegate)
        
        try: self.tree_view.clicked.disconnect(self.on_tree_clicked)
        except: pass
        self.tree_view.clicked.connect(self.on_tree_clicked)

        right_layout.addWidget(self.tree_view)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)
        
        self.load_data()

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
        if index.data(FishingModel.TypeRole) == "store":
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
        """Modo Burst: actualiza estado de pesca. 1=OK, -1=Fail, 0=Reset."""
        logger.info(f"Burst Action Triggered: Status {status}")

        selection = self.tree_view.selectionModel()
        indexes = selection.selectedIndexes()
        
        account_indexes = [idx for idx in indexes if idx.column() == 2 and idx.parent().isValid()]
        
        if not account_indexes:
            account_indexes = [idx for idx in indexes if idx.column() == 0 and idx.parent().isValid()]
            model = self.model
            account_indexes = [model.index(idx.row(), 2, idx.parent()) for idx in account_indexes]

        logger.info(f"Processing {len(account_indexes)} accounts for Burst Action")
        
        if not account_indexes:
            idx = self.tree_view.currentIndex()
            if idx.isValid(): account_indexes = [idx]
            else: return

        if status == 1: self.feedback.play_success()
        elif status == -1: self.feedback.play_fail()

        for index in account_indexes:
            account = index.data(FishingModel.RawDataRole)
            char = account.characters[0] if account.characters else None
            
            if char:
                target_m, target_w = None, None
                
                if status == 0:
                     target_m, target_w = self.controller.get_last_filled_week(char.id, self.current_year)
                else:
                    target_m, target_w = self.controller.get_next_pending_week(char.id, self.current_year)
                
                if target_m and target_w:
                    self.controller.update_fishing_status(char.id, self.current_year, target_m, target_w, status)
                    self.model.update_fishing_status(index, target_m, target_w, status)

        if len(account_indexes) == 1 and status != 0:
             self.move_selection_next()

    def move_selection_next(self):
        current_idx = self.tree_view.currentIndex()
        next_idx = self.tree_view.indexBelow(current_idx)
        
        if next_idx.isValid():
            self.tree_view.setCurrentIndex(next_idx)
            if next_idx.data(FishingModel.TypeRole) == "store":
                 self.move_selection_next()

    def load_data(self):
        self.all_data = self.controller.get_fishing_data(self.server_id, self.current_year)
        
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
        
    def on_year_changed(self, index):
        self.current_year = int(self.combo_year.currentText())
        self.load_data()

    def import_excel(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            try:
                count = self.controller.import_fishing_data_from_excel(file_path, self.server_id)
                QMessageBox.information(self, "Importacion", f"Se importaron datos para {count} cuentas.")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al importar Excel: {str(e)}")

    def apply_filter_and_set_model(self):
        target_store_id = self.combo_store.currentData()
        filtered_data = []
        if target_store_id is None:
            filtered_data = self.all_data
        else:
            filtered_data = [s for s in self.all_data if s['store'].id == target_store_id]
            
        self.model.set_data(filtered_data, self.current_year)
        self.tree_view.expandAll()
        
        for row in range(self.model.rowCount()):
             self.tree_view.setFirstColumnSpanned(row, QModelIndex(), True)

        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
