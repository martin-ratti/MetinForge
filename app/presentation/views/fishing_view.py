from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                             QFrame, QPushButton, QComboBox, QSplitter, QListWidget, QListWidgetItem, QCheckBox,
                             QApplication, QAbstractSpinBox, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from app.application.services.fishing_service import FishingService
from app.utils.shortcuts import register_shortcuts
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
        # Sequential logic is enforced by enabled/disabled state
        if not self.isEnabled(): return

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

    def setOpacity(self, opacity):
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        op = QGraphicsOpacityEffect(self)
        op.setOpacity(opacity)
        self.setGraphicsEffect(op)

class FishingGridWidget(QWidget):
    cellStatusChanged = pyqtSignal(int, int, int) # m, w, status

    def __init__(self, activity_map, year):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)
        
        self.buttons = [] # Track buttons in order

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
                btn.statusChanged.connect(self.handle_button_change)
                mf_layout.addWidget(btn)
                self.buttons.append(btn)
            
            self.layout.addWidget(month_frame)
        
        self.refresh_enable_states()

    def handle_button_change(self, m, w, status):
        self.cellStatusChanged.emit(m, w, status)
        self.refresh_enable_states()

    def refresh_enable_states(self):
        previous_done = True
        
        for btn in self.buttons:
            if previous_done:
                btn.setEnabled(True)
                btn.setOpacity(1.0)
            else:
                btn.setEnabled(False)
                # btn.setOpacity(0.5) optional visual cue
            
            if btn.status == 0:
                previous_done = False
            else:
                previous_done = True

class FishingRow(QFrame):
    selectionChanged = pyqtSignal(bool)
    rowClicked = pyqtSignal(object, Qt.KeyboardModifier)

    def __init__(self, game_account, controller, year):
        super().__init__()
        self.game_account = game_account
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Metin2 Palette: Dark Bg #1a1a1a, Gold Border #5d4d2b
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
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
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        # 0. Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)
        
        # 1st Char as representative
        first_char = game_account.characters[0] if game_account.characters else None
        char_name = first_char.name if first_char else "???"
        display_name = char_name.split('_')[0] if '_' in char_name else char_name
        
        # Labels
        lbl_acc = QLabel(game_account.username)
        lbl_acc.setFixedWidth(130) # Compact Std
        lbl_acc.setStyleSheet("border: none; color: #e0e0e0; font-weight: bold;")
        lbl_acc.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        lbl_name = QLabel(display_name)
        lbl_name.setFixedWidth(130) # Compact Std
        lbl_name.setStyleSheet("border: none; color: #d4af37; font-weight: bold; font-size: 13px;")
        lbl_name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(lbl_acc)
        layout.addWidget(lbl_name)
        
        # Grid
        activity_map = getattr(game_account, 'fishing_activity_map', {})
        self.grid = FishingGridWidget(activity_map, year)
        
        if first_char:
            self.grid.cellStatusChanged.connect(lambda m, w, s: controller.update_fishing_status(first_char.id, year, m, w, s))
        
        layout.addWidget(self.grid, 1)
        # layout.addStretch() # Support full width

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

    def mousePressEvent(self, event):
        self.rowClicked.emit(self, event.modifiers())
        super().mousePressEvent(event)

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
        title.setStyleSheet("font-size: 18px; color: #d4af37; font-weight: bold;")
        title_layout.addWidget(title)
        layout.addWidget(title_widget)
        
        # Header Annual
        header_container = QWidget()
        h_layout = QHBoxLayout()
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(2, 2, 2, 2)
        h_layout.setSpacing(5)
        header_container.setLayout(h_layout)
        
        # Checkbox Placeholder
        lbl_chk = QLabel("")
        lbl_chk.setFixedWidth(24) # 14px indicator + margins
        h_layout.addWidget(lbl_chk)

        lbl_h_acc = QLabel("CUENTA")
        lbl_h_acc.setFixedWidth(130) # Compact Std
        lbl_h_acc.setStyleSheet("color: #a0a0a0; font-weight: bold; font-size: 10px;")
        h_layout.addWidget(lbl_h_acc)
        
        lbl_h1 = QLabel("PESCADOR")
        lbl_h1.setFixedWidth(130) # Compact Std
        lbl_h1.setStyleSheet("color: #a0a0a0; font-weight: bold; font-size: 10px;")
        h_layout.addWidget(lbl_h1)
        
        grid_header = FishingHeaderWidget()
        h_layout.addWidget(grid_header, 1) # Full width
        # h_layout.addStretch()
        layout.addWidget(header_container)

        # Cuentas 
        self.rows = [] # Track rows
        accounts = store_data.get('accounts', [])
        for game_account in accounts:
             row = FishingRow(game_account, controller, year)
             self.rows.append(row)
             layout.addWidget(row)


# --- MAIN VIEW ---

class FishingView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = FishingService()
        self.current_year = datetime.date.today().year
        self.current_year = datetime.date.today().year
        self.data_cache = []
        self.all_data = [] # New: Store all data
        self.rows = [] # New: Track rows
        self.selected_store_email = None
        self.last_clicked_row = None
        
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
        
        left_title = QLabel("Pesca Anual")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d4af37;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        left_layout.addLayout(header_left)
        
        # Store List
        # Store List REMOVED
        # left_layout.addWidget(self.store_list)
        
        # --- RIGHT PANEL: Details ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # Top Bar Right
        top_bar = QHBoxLayout()
        lbl_server = QLabel(f"{self.server_name.title()}")
        lbl_server.setStyleSheet("font-size: 14px; font-weight: bold; color: #d4af37; background-color: #263238; border: 1px solid #d4af37; border-radius: 4px; padding: 4px 8px;")
        
        self.combo_year = QComboBox()
        for y in range(2025, 2031):
            self.combo_year.addItem(str(y))
        self.combo_year.setCurrentText(str(self.current_year))
        self.combo_year.setStyleSheet("padding: 5px; background-color: #37474f; color: white;")
        self.combo_year.currentIndexChanged.connect(self.on_year_changed)
        
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

        top_bar.addWidget(lbl_server)
        top_bar.addStretch()
        
        # Store Filter
        self.combo_store = QComboBox()
        self.combo_store.setMinimumWidth(150)
        self.combo_store.setStyleSheet("padding: 5px; background-color: #37474f; color: white; border: 1px solid #546e7a; border-radius: 4px;")
        self.combo_store.currentIndexChanged.connect(self.on_store_filter_changed)
        top_bar.addWidget(self.combo_store)
        
        top_bar.addWidget(QLabel("Año:"))
        top_bar.addWidget(self.combo_year)
        
        btn_select_all = QPushButton("Seleccionar Todo")
        btn_select_all.clicked.connect(self.select_all_rows)
        btn_select_all.setFixedHeight(30)
        btn_select_all.setStyleSheet("QPushButton { background-color: #455a64; color: white; border: 1px solid #607d8b; border-radius: 4px; font-weight: bold; padding: 0 10px; } QPushButton:hover { background-color: #546e7a; }")
        top_bar.addWidget(btn_select_all)
        
        top_bar.addWidget(btn_help)
        right_layout.addLayout(top_bar)
        
        # Scroll Area
        from app.utils.styles import SCROLLBAR_STYLESHEET
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True) # Vertical resize
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }" + SCROLLBAR_STYLESHEET)
        
        self.content_container = QWidget()
        self.content_container.setStyleSheet("background-color: transparent;") # Prevent white background
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_container.setLayout(self.content_layout)
        
        self.scroll.setWidget(self.content_container)
        right_layout.addWidget(self.scroll, 1)
        
        # --- BATCH ACTIONS TOOLBAR (Floating at bottom) ---
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
        batch_layout.setContentsMargins(20, 0, 20, 0)
        
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
        
        right_layout.addWidget(self.batch_toolbar)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)
        
        # Init Shortcuts
        self.setup_shortcuts()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


    def load_data(self):
        # Fetch all data
        self.all_data = self.controller.get_fishing_data(self.server_id, self.current_year)
        
        self.clear_details()
        self.selected_store_email = None
        
        # Populate Filter
        self.combo_store.blockSignals(True)
        self.combo_store.clear()
        self.combo_store.addItem("Todos", None)
        
        if self.all_data:
            sorted_stores = sorted(self.all_data, key=lambda x: x['store'].email)
            for item in sorted_stores:
                store = item['store']
                self.combo_store.addItem(store.email, store.id)
        self.combo_store.blockSignals(False)
        
        self.filter_rows()

    def on_store_filter_changed(self, index):
        self.filter_rows()
        
    def filter_rows(self):
        self.clear_details()
        self.rows = []
        
        target_store_id = self.combo_store.currentData()
        
        filtered_data = []
        if target_store_id is None:
            filtered_data = self.all_data
        else:
            filtered_data = [s for s in self.all_data if s['store'].id == target_store_id]
            
        if not filtered_data:
            return

        # Reuse existing layout (cleared by clear_details)
        content_layout = self.content_layout
        
        for store_data in filtered_data:
            # Create a "Block" for each store
            store_block = QWidget()
            block_layout = QVBoxLayout()
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(0)
            store_block.setLayout(block_layout)
            
            # --- Store Header ---
            header_widget = self.create_store_header(store_data['store'].email)
            block_layout.addWidget(header_widget)
            
            # --- Accounts ---
            accounts = store_data.get('accounts', [])
            for game_account in accounts:
                 row = FishingRow(game_account, self.controller, self.current_year)
                 row.selectionChanged.connect(self.update_batch_toolbar)
                 row.rowClicked.connect(self.on_row_clicked)
                 self.rows.append(row)
                 block_layout.addWidget(row)
            
            content_layout.addWidget(store_block)
            
        self.update_batch_toolbar()
        self.update_batch_toolbar()
    
    def create_store_header(self, email):
        header_container = QWidget()
        header_container.setStyleSheet("background-color: #102027; border-bottom: 2px solid #546e7a; margin-top: 5px;")
        
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)
        header_container.setLayout(v_layout)
        
        # Title
        title = QLabel(f"📧 {email}")
        title.setStyleSheet("font-size: 14px; color: #d4af37; font-weight: bold; padding: 5px;")
        v_layout.addWidget(title)
        
        # Column Headers
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(2, 2, 2, 2)
        h_layout.setSpacing(5)
        
        lbl_chk = QLabel("")
        lbl_chk.setFixedWidth(24)
        h_layout.addWidget(lbl_chk)

        lbl_h_acc = QLabel("CUENTA")
        lbl_h_acc.setFixedWidth(130) # Compact Std
        lbl_h_acc.setStyleSheet("color: #a0a0a0; font-weight: bold; font-size: 10px;")
        h_layout.addWidget(lbl_h_acc)
        
        lbl_h1 = QLabel("PESCADOR")
        lbl_h1.setFixedWidth(130) # Compact Std
        lbl_h1.setStyleSheet("color: #a0a0a0; font-weight: bold; font-size: 10px;")
        h_layout.addWidget(lbl_h1)
        
        grid_header = FishingHeaderWidget()
        h_layout.addWidget(grid_header, 1) 
        
        v_layout.addLayout(h_layout)
        return header_container

    # on_store_selected REMOVED

    # show_store_details REMOVED

    def clear_details(self):
        while self.content_layout.count():
             item = self.content_layout.takeAt(0)
             if item.widget(): item.widget().deleteLater()
        self.current_details_widget = None

    def on_year_changed(self):
        self.current_year = int(self.combo_year.currentText())
        self.load_data()

    def setup_shortcuts(self):
        register_shortcuts(self, {
            'Ctrl+A': self.select_all_rows,
            'Ctrl+D': self.deselect_all_rows,
        })
        
    def keyPressEvent(self, event):
        """Handle 1, 2, 3 shortcuts safely (ignore if editing input)"""
        text = event.text()
        if text in ['1', '2', '3']:
            # Check if an input widget has focus
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, (QAbstractSpinBox, QLineEdit)):
                super().keyPressEvent(event)
                return

            # Trigger Batch Action
            status_map = {'1': 1, '2': -1, '3': 0}
            self.apply_batch_status(status_map[text])
            event.accept()
        else:
            super().keyPressEvent(event)

    def select_all_rows(self):
        for row in self.rows:
            row.set_selected(True)

    def deselect_all_rows(self):
        for row in self.rows:
            row.set_selected(False)

    def on_row_clicked(self, row, modifiers):
        if row not in self.rows: return
        
        idx = self.rows.index(row)
        
        if modifiers & Qt.KeyboardModifier.ShiftModifier and hasattr(self, 'last_clicked_row') and self.last_clicked_row in self.rows:
            start = self.rows.index(self.last_clicked_row)
            end = idx
            step = 1 if start < end else -1
            for i in range(start, end + step, step):
                self.rows[i].set_selected(True)
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            row.set_selected(not row.is_selected())
        else:
            # Check if we should implement single click select or just toggle
            pass
            
        self.last_clicked_row = row

    def update_batch_toolbar(self):
        selected = [r for r in self.rows if r.is_selected()]
        count = len(selected)
        self.lbl_batch_count.setText(f"{count} seleccionadas")
        self.batch_toolbar.setVisible(count > 0)

    def show_help(self):
        from app.presentation.views.dialogs.help_shortcuts_dialog import HelpShortcutsDialog
        dialog = HelpShortcutsDialog(self)
        dialog.exec()

    def apply_batch_status(self, status):
        from PyQt6.QtWidgets import QMessageBox
        
        selected_rows = [r for r in self.rows if r.is_selected()]
        if not selected_rows: return
        
        count = 0
        for row in selected_rows:
            char = row.game_account.characters[0] if row.game_account.characters else None
            if char:
                # Sequential Logic: Find next pending WEEK
                # Fishing is (Month, Week)
                # We need a controller method: get_next_pending_week(char_id, year)
                # returning (month, week) tuple
                
                next_m, next_w = self.controller.get_next_pending_week(char.id, self.current_year)
                
                # Careful with Reset (0). Logic: If 0, target LAST completed?
                # For simplicity, stick to next_pending for now or enforce progression
                # Just applying to the calculated slot
                
                target_m, target_w = next_m, next_w
                if status == 0 and (target_m > 1 or target_w > 1):
                     # If resetting, maybe we want to undo the PREVIOUS one?
                     # Let's simple apply to pending for now to avoid complexity or just current
                     pass

                self.controller.update_fishing_status(char.id, self.current_year, target_m, target_w, status)
                count += 1
        
        self.load_data()
        QMessageBox.information(self, "Acción Batch - Pesca", f"Se actualizaron {count} cuentas.")
