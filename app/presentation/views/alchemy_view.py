from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                             QFrame, QGroupBox, QGridLayout, QSpinBox, QListWidget, QSplitter,
                             QPushButton, QInputDialog, QMessageBox, QListWidgetItem, QComboBox,
                             QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from app.application.services.alchemy_service import AlchemyService
from app.presentation.views.widgets.daily_grid import DailyGridWidget
from app.utils.shortcuts import register_shortcuts
import datetime

class AlchemyRow(QFrame):
    """ Fila individual: Cuenta | Slots | PJ Principal | Grid | Cords Hoy | Total Cords """
    editRequested = pyqtSignal(object) # game_account object
    selectionChanged = pyqtSignal(bool)
    rowClicked = pyqtSignal(object, Qt.KeyboardModifier) # (self, modifiers)
    cordsChanged = pyqtSignal(int, int, int)  # (account_id, day_index, cords_count)

    def __init__(self, game_account, controller, event_id, total_days, current_day=1, cords_summary=None):
        super().__init__()
        self.game_account = game_account
        self.controller = controller
        self.event_id = event_id
        self.current_day = current_day
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        # Metin2 Palette - Compact Style
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-bottom: 1px solid #333; /* Only bottom border for separator feel */
                border-radius: 0px;
                margin: 0px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """)
        
        # Use QHBoxLayout to match Header
        layout = QHBoxLayout()
        # Compact Margins: Left, Top, Right, Bottom
        layout.setContentsMargins(2, 2, 2, 2) 
        layout.setSpacing(5)
        self.setLayout(layout)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # 0. Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)

        # 3. Nombre Personaje (Principal/Visual)
        # Sort characters by ID to ensure we pick the first created one (The Alchemist)
        chars = sorted(game_account.characters, key=lambda x: x.id) if game_account.characters else []
        first_char = chars[0] if chars else None

        # Grid Activity Map
        activity_map = getattr(game_account, 'current_event_activity', {})
        
        from app.presentation.views.widgets.daily_grid import DailyGridWidget
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
        lbl_account.setFixedWidth(130) # Compact Std
        lbl_account.setStyleSheet("border: none; color: #e0e0e0; font-weight: bold; font-size: 12px;")
        
        # 2. Cantidad Slots
        real_slots = len(game_account.characters)
        lbl_slots = QLabel(str(real_slots))
        lbl_slots.setFixedWidth(40)
        lbl_slots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_slots.setStyleSheet("background-color: #2b2b2b; border: 1px solid #5d4d2b; color: #d4af37; border-radius: 2px; padding: 2px;")

        # 3. Nombre Personaje
        # Just show the name directly. The Import Controller ensures the first one is the Alchemist.
        display_name = first_char.name if first_char else "-"
        
        lbl_char = QLabel(display_name)
        lbl_char.setFixedWidth(130) # Compact Std
        lbl_char.setStyleSheet("border: none; color: #d4af37; font-weight: bold; font-size: 13px;")
        
        # Ensure clicks on labels propagate to the row
        lbl_account.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lbl_slots.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lbl_char.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        layout.addWidget(lbl_account)
        layout.addWidget(lbl_slots)
        layout.addWidget(lbl_char)
        layout.addWidget(grid_widget, 1) # Stretch factor 1 to take remaining space
        
        # 4. CORDS HOY - SpinBox para ingresar cords del día actual
        self.spin_cords = QSpinBox()
        self.spin_cords.setRange(0, 999)
        self.spin_cords.setFixedWidth(60)
        self.spin_cords.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_cords.setStyleSheet("""
            QSpinBox {
                background-color: #2b2b2b;
                color: #00ff00;
                border: 1px solid #5d4d2b;
                border-radius: 3px;
                padding: 2px;
                font-size: 12px;
                font-weight: bold;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 14px;
            }
        """)
        # Cargar valor actual de cords si existe
        if cords_summary and game_account.id in cords_summary:
            daily_cords = controller.get_daily_cords(game_account.id, event_id)
            self.spin_cords.setValue(daily_cords.get(current_day, 0))
        
        self.spin_cords.valueChanged.connect(self._on_cords_changed)
        layout.addWidget(self.spin_cords)

    def _on_cords_changed(self, value):
        """Llamado cuando cambia el spinbox de cords"""
        if self.controller and self.event_id:
            self.controller.update_daily_cords(
                self.game_account.id, 
                self.event_id, 
                self.current_day, 
                value
            )
            self.cordsChanged.emit(self.game_account.id, self.current_day, value)

        
    def _on_checkbox_changed(self, state):
        selected = (state == Qt.CheckState.Checked.value)
        self.update_selection_style(selected)
        self.selectionChanged.emit(selected)

    def is_selected(self):
        return self.checkbox.isChecked()

    def set_selected(self, selected):
        self.checkbox.setChecked(selected)
        # Style will be updated by checkbox signal

    def update_selection_style(self, selected):
        if selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2d2d1b;
                    border: 1px solid #d4af37;
                    border-radius: 2px;
                    margin: 0px;
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

    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Editar Cuenta")
        edit_action.triggered.connect(lambda: self.editRequested.emit(self.game_account))
        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        self.rowClicked.emit(self, event.modifiers())
        # Let it propagate so focus works if needed
        super().mousePressEvent(event)

class StoreDetailsWidget(QWidget):
    def __init__(self, store_data, controller, view_parent, event_id, total_days, current_day=1, cords_summary=None):
        super().__init__()
        self.controller = controller
        self.rows = [] # Track account rows
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.setLayout(layout)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent;")
        
        # Título
        title_widget = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 0, 5) 
        title_widget.setLayout(title_layout)
        title = QLabel(f"📧 {store_data['store'].email}")
        title.setStyleSheet("font-size: 18px; color: #d4af37; font-weight: bold;")
        title_layout.addWidget(title)
        layout.addWidget(title_widget)
        
        # --- HEADER ---
        # Must match AlchemyRow layout EXACTLY
        header_container = QWidget()
        header_layout = QHBoxLayout()
        # Match AlchemyRow margins
        header_layout.setContentsMargins(2, 2, 2, 2) 
        header_layout.setSpacing(5)
        header_container.setLayout(header_layout)
        
        # Style header container to match row structure visually but distinct
        header_container.setStyleSheet("""
            QWidget {
                background-color: #102027;
                border: 1px solid #37474f;
                border-radius: 4px;
                margin-bottom: 5px;
            }
            QLabel {
                border: none;
            }
        """)
        
        # Placeholder para el checkbox
        checkbox_placeholder = QLabel("")
        checkbox_placeholder.setFixedWidth(20)
        header_layout.addWidget(checkbox_placeholder)
        
        lbl_h1 = QLabel("CUENTA")
        lbl_h1.setFixedWidth(130) # Compact Std
        lbl_h1.setStyleSheet("color: #a0a0a0; font-size: 10px; font-weight: bold;")
        
        lbl_h2 = QLabel("SLOTS")
        lbl_h2.setFixedWidth(40)
        lbl_h2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_h2.setStyleSheet("color: #a0a0a0; font-size: 10px; font-weight: bold;")
        
        lbl_h3 = QLabel("MEZCLADOR")
        lbl_h3.setFixedWidth(130) # Compact Std
        lbl_h3.setStyleSheet("color: #a0a0a0; font-size: 10px; font-weight: bold;")
        
        header_layout.addWidget(lbl_h1)
        header_layout.addWidget(lbl_h2)
        header_layout.addWidget(lbl_h3)
        
        from app.views.widgets.daily_grid import DailyGridHeaderWidget
        header_grid = DailyGridHeaderWidget(total_days=total_days)
        header_layout.addWidget(header_grid, 1) # Stretch factor 1
        
        # Headers para CORDS (TOTAL se muestra en el panel de alquimias)
        lbl_h_cords = QLabel("CORDS")
        lbl_h_cords.setFixedWidth(60)
        lbl_h_cords.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_h_cords.setStyleSheet("color: #00ff00; font-size: 10px; font-weight: bold;")
        header_layout.addWidget(lbl_h_cords)
        
        layout.addWidget(header_container)
        
        # Cuentas
        accounts = store_data.get('accounts', [])
        for game_account in accounts:
            row_widget = AlchemyRow(
                game_account, controller, event_id, total_days, 
                current_day=current_day, cords_summary=cords_summary
            )
            row_widget.editRequested.connect(view_parent.on_edit_account_requested)
            row_widget.rowClicked.connect(view_parent.on_row_clicked)
            # Conectar cambio de cords para actualizar total global
            row_widget.cordsChanged.connect(view_parent.on_cords_changed)
            self.rows.append(row_widget)
            layout.addWidget(row_widget)


class AlchemyView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = AlchemyService()
        
        self.data = [] 
        self.selected_email = None
        self.current_event = None
        self.events_cache = []
        self.events_cache = []
        self.all_data = [] # New: Store all data for filtering
        self.rows = [] # New: Track all rows directly
        self.last_clicked_row = None
        
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
            QPushButton:hover {
                background-color: #800000;
            }
        """)
        
        left_title = QLabel(f"{self.server_name}")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d4af37;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        left_layout.addLayout(header_left)
        
        btn_add_email = QPushButton("📧+ Correo") 
        btn_add_email.setFixedWidth(110)
        btn_add_email.setFixedHeight(30)
        btn_add_email.clicked.connect(self.prompt_add_email)
        btn_add_email.setStyleSheet("QPushButton { background-color: #1565c0; color: white; border: 1px solid #1e88e5; border-radius: 4px; font-weight: bold; font-size: 13px; } QPushButton:hover { background-color: #1e88e5; }")
        
        btn_import = QPushButton("📥 Importar")
        btn_import.setFixedWidth(100)
        btn_import.setFixedHeight(30)
        btn_import.clicked.connect(self.on_import_requested)
        btn_import.setStyleSheet("QPushButton { background-color: #455a64; color: white; border: 1px solid #607d8b; border-radius: 4px; font-weight: bold; font-size: 13px; } QPushButton:hover { background-color: #607d8b; }")
        
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

        email_toolbar = QHBoxLayout()
        email_toolbar.addWidget(btn_add_email)
        email_toolbar.addWidget(btn_import)
        email_toolbar.addWidget(btn_help)
        email_toolbar.addStretch()
        left_layout.addLayout(email_toolbar)
        

        
        # --- WIDGET DE ALQUIMIAS ---
        from app.presentation.views.widgets.alchemy_counters_widget import AlchemyCountersWidget
        self.alchemy_counters_widget = AlchemyCountersWidget(
            controller=self.controller,
            event_id=None  # Se actualizará cuando se seleccione un evento
        )
        left_layout.addWidget(self.alchemy_counters_widget)
        
        # --- RIGHT PANEL ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        header_right = QHBoxLayout()
        header_right.setSpacing(10)
        
        lbl_server = QLabel(f"{self.server_name.title()}")
        lbl_server.setStyleSheet("font-size: 14px; font-weight: bold; color: #d4af37; background-color: #263238; border: 1px solid #d4af37; border-radius: 4px; padding: 4px 8px;")
        header_right.addWidget(lbl_server)
        
        header_right.addStretch()
        
        # Store Filter
        self.combo_store = QComboBox()
        self.combo_store.setMinimumWidth(150)
        self.combo_store.setStyleSheet("padding: 5px; background-color: #263238; color: white; border: 1px solid #546e7a; border-radius: 4px;")
        self.combo_store.currentIndexChanged.connect(self.on_store_filter_changed)
        header_right.addWidget(self.combo_store)
        
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
        
        self.btn_select_all = QPushButton("Seleccionar Todo")
        self.btn_select_all.clicked.connect(self.select_all_rows)
        self.btn_select_all.setFixedHeight(30)
        self.btn_select_all.setStyleSheet("QPushButton { background-color: #455a64; color: white; border: 1px solid #607d8b; border-radius: 4px; font-weight: bold; padding: 0 10px; } QPushButton:hover { background-color: #546e7a; }")

        header_right.addWidget(self.btn_select_all)
        header_right.addWidget(self.btn_add_account)
        right_layout.addLayout(header_right)
        

        
        from app.utils.styles import SCROLLBAR_STYLESHEET
        self.scroll_details = QScrollArea()
        self.scroll_details.setWidgetResizable(True)
        self.scroll_details.setStyleSheet("QScrollArea { border: none; background-color: transparent; }" + SCROLLBAR_STYLESHEET)
        
        # The details_container and details_layout are no longer needed as setWidget will replace the entire content
        right_layout.addWidget(self.scroll_details, 1) # Stretch factor 1 to fill space
        
        # --- BATCH ACTIONS TOOLBAR (Floating at bottom) ---
        self.batch_toolbar = QFrame()
        self.batch_toolbar.setFixedHeight(50)
        self.batch_toolbar.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-top: 2px solid #5d4d2b;
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
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
        """Select all account rows in the current detail view."""
        for row in self.rows:
            row.set_selected(True)

    def deselect_all_rows(self):
        """Deselect all account rows."""
        for row in self.rows:
            row.set_selected(False)

    def apply_batch_status(self, status):
        """Apply a status to all selected rows based on their next sequential day."""
        selected_rows = [row for row in self.rows if row.is_selected()]
        if not selected_rows:
            return
            
        if not self.current_event:
            return
            
        count = 0
        for row in selected_rows:
            char = row.game_account.characters[0] if row.game_account.characters else None
            if char:
                day_to_update = 1
                if status == 0:
                    next_day = self.controller.get_next_pending_day(char.id, self.current_event.id)
                    day_to_update = max(1, next_day - 1)
                else:
                    day_to_update = self.controller.get_next_pending_day(char.id, self.current_event.id)

                self.controller.update_daily_status(
                    char.id, day_to_update, status, event_id=self.current_event.id
                )
                count += 1
        
        # Refresh view
        self.load_data() 
        QMessageBox.information(self, "Acción Batch", f"Se actualizaron {count} cuentas.")

    def on_row_clicked(self, row, modifiers):
        if row not in self.rows:
            return
            
        idx = self.rows.index(row)
        
        if modifiers & Qt.KeyboardModifier.ShiftModifier and self.last_clicked_row in self.rows:
            # Range selection
            start_idx = self.rows.index(self.last_clicked_row)
            end_idx = idx
            
            # Select everything in between
            step = 1 if start_idx < end_idx else -1
            for i in range(start_idx, end_idx + step, step):
                self.rows[i].set_selected(True)
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            # Toggle individual
            row.set_selected(not row.is_selected())
        else:
            # Single click selection (optional, user said "Atajos Obligatorio" maybe they want this too)
            # Keeping it as toggle for now to be safe, or just update last_clicked
            pass
            
        self.last_clicked_row = row
        self.update_batch_toolbar()

    def update_batch_toolbar(self):
        selected_count = sum(1 for row in self.rows if row.is_selected())
        self.lbl_batch_count.setText(f"{selected_count} seleccionadas")
        self.batch_toolbar.setVisible(selected_count > 0)

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
        
        # Actualizar widget de alquimias
        if hasattr(self, 'alchemy_counters_widget'):
            eid = self.current_event.id if self.current_event else None
            self.alchemy_counters_widget.set_event(eid)
        
        self.load_data()

    def prompt_create_event(self):
        from app.presentation.views.dialogs.event_dialog import EventDialog
        dialog = EventDialog(self)
        # Pre-fill name suggestion
        dialog.txt_name.setText(f"Evento {len(self.events_cache) + 1}")
        
        if dialog.exec():
            name, days = dialog.get_data()
            if not name: return
            
            new_ev = self.controller.create_alchemy_event(self.server_id, name, days)
            if new_ev:
                self.load_events()
                # Select the new event SAFELY by ID
                target_id = new_ev.id
                for i in range(self.combo_events.count()):
                    ev_item = self.combo_events.itemData(i)
                    if ev_item and ev_item.id == target_id:
                        self.combo_events.setCurrentIndex(i)
                        break
            else:
                QMessageBox.warning(self, "Error", "No se pudo crear el evento.")

    def on_event_changed(self, index):
        if index < 0: return
        self.current_event = self.combo_events.itemData(index)
        # Actualizar widget de alquimias
        if hasattr(self, 'alchemy_counters_widget'):
            eid = self.current_event.id if self.current_event else None
            self.alchemy_counters_widget.set_event(eid)
        self.load_data()

    def on_store_filter_changed(self, index):
        self.filter_rows()



    def load_data(self):
        if not self.current_event:
            self.all_data = []
            self.clear_details()
            return

        # Fetch all data
        self.all_data = self.controller.get_alchemy_dashboard_data(self.server_id, event_id=self.current_event.id)
        
        self.clear_details()
        self.btn_add_account.setVisible(False)
        self.selected_email = None
        
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

        # Container for the unified list
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10) # Spacing between store blocks
        content_widget.setLayout(content_layout)
        
        eid = self.current_event.id if self.current_event else None
        total_days = self.current_event.total_days if self.current_event else 30
        cords_summary = self.controller.get_event_cords_summary(eid) if eid else {}
        current_day = self._calculate_current_day()

        for store_data in filtered_data:
            # Create a "Block" for each store
            store_block = QWidget()
            block_layout = QVBoxLayout()
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(0)
            store_block.setLayout(block_layout)
            
            # --- Store Header (The "Yellow Row" separator) ---
            # Reuse logic from StoreDetailsWidget but simplified since we are unifying
            header_widget = self.create_store_header(store_data['store'].email, total_days)
            block_layout.addWidget(header_widget)
            
            # --- Accounts ---
            accounts = store_data.get('accounts', [])
            for game_account in accounts:
                row_widget = AlchemyRow(
                    game_account, self.controller, eid, total_days, 
                    current_day=current_day, cords_summary=cords_summary
                )
                row_widget.editRequested.connect(self.on_edit_account_requested)
                row_widget.rowClicked.connect(self.on_row_clicked)
                row_widget.cordsChanged.connect(self.on_cords_changed)
                row_widget.selectionChanged.connect(self.update_batch_toolbar)
                
                self.rows.append(row_widget)
                block_layout.addWidget(row_widget)
            
            content_layout.addWidget(store_block)

        self.scroll_details.setWidget(content_widget)
        self.update_batch_toolbar()
        
    def create_store_header(self, email, total_days):
        # Header Container
        header_container = QWidget()
        header_container.setStyleSheet("background-color: #102027; border-bottom: 2px solid #546e7a; margin-top: 10px;")
        
        # Main vertical layout to hold Title + GridHeader
        main_v = QVBoxLayout()
        main_v.setContentsMargins(0, 0, 0, 0)
        main_v.setSpacing(5)
        header_container.setLayout(main_v)
        
        # 1. Email Title (The "Visual Separation")
        title_lbl = QLabel(f"📧 {email}")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #d4af37; padding: 5px;")
        main_v.addWidget(title_lbl)
        
        # 2. Columns Header
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(2, 2, 2, 2)
        h_layout.setSpacing(5)
        
        # Checkbox Placeholder
        lbl_chk = QLabel("")
        lbl_chk.setFixedWidth(24)
        h_layout.addWidget(lbl_chk)
        
        lbl_h1 = QLabel("CUENTA")
        lbl_h1.setFixedWidth(130)
        lbl_h1.setStyleSheet("color: #eceff1; font-size: 11px; font-weight: bold;")
        
        lbl_h2 = QLabel("SLOTS")
        lbl_h2.setFixedWidth(40)
        lbl_h2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_h2.setStyleSheet("color: #eceff1; font-size: 11px; font-weight: bold;")
        
        lbl_h3 = QLabel("MEZCLADOR")
        lbl_h3.setFixedWidth(130)
        lbl_h3.setStyleSheet("color: #eceff1; font-size: 11px; font-weight: bold;")
        
        h_layout.addWidget(lbl_h1)
        h_layout.addWidget(lbl_h2)
        h_layout.addWidget(lbl_h3)
        
        from app.presentation.views.widgets.daily_grid import DailyGridHeaderWidget
        header_grid = DailyGridHeaderWidget(total_days=total_days)
        h_layout.addWidget(header_grid, 1)
        
        lbl_h_cords = QLabel("CORDS")
        lbl_h_cords.setFixedWidth(60)
        lbl_h_cords.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_h_cords.setStyleSheet("color: #00ff00; font-size: 10px; font-weight: bold;")
        h_layout.addWidget(lbl_h_cords)
        
        main_v.addLayout(h_layout)
        
        return header_container

    def clear_details(self):
        if hasattr(self, 'scroll_details') and self.scroll_details.widget():
            widget = self.scroll_details.widget()
            if widget:
                widget.deleteLater()
            self.scroll_details.takeWidget()

    def on_cords_changed(self, account_id, day_index, cords_count):
        """Llamado cuando cambia el valor de cords en alguna fila"""
        # Actualizar el total global en el widget de alquimias
        if hasattr(self, 'alchemy_counters_widget'):
            self.alchemy_counters_widget.update_cords_display()

    def prompt_add_email(self):
        email, ok = QInputDialog.getText(self, "Nuevo Correo", "Dirección de Email:")
        if ok and email:
            email = email.strip()
            if self.controller.create_store_email(email):
                QMessageBox.information(self, "Éxito", f"Correo '{email}' agregado.")
                self.load_data()
            else:
                 QMessageBox.warning(self, "Error", "No se pudo crear el correo.")

    def prompt_add_game_account(self):
        if not self.selected_email: return
        from app.presentation.views.dialogs.account_dialog import AccountDialog
        dialog = AccountDialog(self, email=self.selected_email)
        dialog.txt_email.setReadOnly(True)
        
        if dialog.exec():
            _, username, pj_name, slots = dialog.get_data()
            if self.controller.create_game_account(self.server_id, username, slots, self.selected_email, pj_name):
                 QMessageBox.information(self, "Éxito", "Cuenta creada.")
                 self.load_data()
            else:
                 QMessageBox.warning(self, "Error", "Error al crear cuenta.")

    def on_edit_account_requested(self, game_account):
        first_char = game_account.characters[0] if game_account.characters else None
        current_pj_name = first_char.name.split('_')[0] if first_char else ""
        from app.presentation.views.dialogs.account_dialog import AccountDialog
        current_slots = len(game_account.characters)
        current_email = game_account.store_account.email
        
        dialog = AccountDialog(self, username=game_account.username, slots=current_slots, email=current_email, edit_mode=True)
        dialog.txt_pj_name.setText(current_pj_name)
        
        if dialog.exec():
            new_email, new_name, new_pj_name, new_slots = dialog.get_data()
            if self.controller.update_game_account(game_account.id, new_name, new_slots, new_email):
                 QMessageBox.information(self, "Éxito", "Cuenta actualizada.")
                 self.load_data()
            else:
                 QMessageBox.warning(self, "Error", "No se pudo actualizar.")

    def on_import_requested(self):
        from PyQt6.QtWidgets import QFileDialog
        from app.application.services.import_service import ImportService
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Cuentas", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
            
        try:
            # Check extension
            if file_path.lower().endswith('.csv'):
                 QMessageBox.warning(self, "Aviso", "La importación de CSV con el nuevo formato no está soportada aún. Use Excel (.xlsx).")
                 return

            # Instantiate service (creates its own session or we could pass one if we wanted shared transaction)
            importer = ImportService() 
            
            result = importer.import_from_excel(file_path, self.server_id)
            
            if result.get("success"):
                processed = result.get("processed_accounts", 0)
                QMessageBox.information(self, "Éxito", f"Importación completada.\nCuentas procesadas: {processed}")
                
                # Refresh view by reloading data
                # Identify an email to select? Maybe the last one or first one created?
                # For now just reload.
                self.load_data() 
            else:
                QMessageBox.warning(self, "Error de Importación", f"Error: {result.get('error')}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error crítico al importar: {str(e)}")

    def show_help(self):
        from app.presentation.views.dialogs.help_shortcuts_dialog import HelpShortcutsDialog
        dialog = HelpShortcutsDialog(self)
        dialog.exec()

    def _calculate_current_day(self):
        """
        Calcula el día actual del evento basándose en la fecha de creación.
        Retorna 1 si no hay evento seleccionado o si el evento fue creado hoy.
        """
        if not self.current_event:
            return 1
        
        created_at = self.current_event.created_at
        if not created_at:
            return 1
        
        today = datetime.date.today()
        delta = (today - created_at).days + 1  # +1 porque el día 1 es el día de creación
        
        # Limitar al máximo de días del evento
        max_days = self.current_event.total_days if self.current_event.total_days else 30
        return min(max(1, delta), max_days)

