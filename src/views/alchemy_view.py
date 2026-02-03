from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                             QFrame, QGroupBox, QGridLayout, QSpinBox, QListWidget, QSplitter,
                             QPushButton, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from src.controllers.alchemy_controller import AlchemyController
from src.views.widgets.daily_grid import DailyGridWidget

class AlchemyRow(QFrame):
    """ Fila individual: Cuenta | Slots | PJ Principal | Grid """
    editRequested = pyqtSignal(object) # game_account object

    def __init__(self, game_account, controller):
        super().__init__()
        self.game_account = game_account
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: #263238; border-radius: 4px; margin-bottom: 2px;")
        
        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.setLayout(layout)

        # 1. Nombre Cuenta (Ej: ALOLA)
        lbl_account = QLabel(game_account.username)
        lbl_account.setFixedWidth(120)
        lbl_account.setStyleSheet("color: #b0bec5; font-weight: bold; font-size: 12px;")
        
        # 2. Cantidad Slots (Ej: 5)
        real_slots = len(game_account.characters)
        lbl_slots = QLabel(str(real_slots))
        lbl_slots.setFixedWidth(30)
        lbl_slots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_slots.setStyleSheet("background-color: #37474f; color: #eceff1; border-radius: 2px; padding: 2px;")

        # 3. Nombre Personaje (Principal/Visual)
        # Tomamos el primero si existe, si no "Sin PJ"
        first_char = game_account.characters[0] if game_account.characters else None
        char_name = first_char.name if first_char else "-"
        
        # Limpiamos el nombre si tiene sufijo interno tipo "_1" y el usuario no quiere verlo?
        # El usuario dijo "le pongo el nombre que tiene la cuenta en general".
        # Si guardamos "Reynares_1", mostramos "Reynares"?
        # Si el usuario pone "Reynares" en la UI, nosotros guardaremos Reynares_1, Reynares_2...
        # Asi que mostramos el "base name" o el nombre del primero.
        # Asumamos que el nombre del primer PJ es el representativo.
        display_name = char_name.split('_')[0] if '_' in char_name else char_name
        
        lbl_char = QLabel(display_name)
        lbl_char.setFixedWidth(120)
        lbl_char.setStyleSheet("color: #4dd0e1; font-weight: bold; font-size: 13px;")
        
        # 4. Grid
        # Usamos la actividad del PRIMER personaje para visualizar la fila?
        # O necesitamos un grid que consolide?
        # El requerimiento dice "que cada cuenta tenga 5 personajes es solo para visualizar".
        # Asumiremos que el Grid refleja el estado de la actividad "del dia" para esa cuenta.
        # Usaremos el primer personaje como proxy para guardar la data.
        
        activity_map = {}
        if first_char:
            for log in first_char.daily_cors:
                activity_map[log.date.day] = log.status_code

        from src.views.widgets.daily_grid import DailyGridWidget
        grid_widget = DailyGridWidget(activity_map)
        
        if first_char:
            char_id = first_char.id
            grid_widget.statusChanged.connect(lambda day, status, cid=char_id: controller.update_daily_status(cid, day, status))
        
        layout.addWidget(lbl_account, 0, 0)
        layout.addWidget(lbl_slots, 0, 1)
        layout.addWidget(lbl_char, 0, 2)
        layout.addWidget(grid_widget, 0, 3)
        
        layout.setColumnStretch(3, 1) 
        
    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        action_edit = menu.addAction("✏️ Editar Cuenta")
        action = menu.exec(event.globalPos())
        
        if action == action_edit:
            self.editRequested.emit(self.game_account)

class StoreDetailsWidget(QWidget):
    """ Widget que muestra el contenido de una tienda seleccionada """
    def __init__(self, store_data, controller, view_parent):
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        
        # Título de la tienda
        title = QLabel(f"📧 {store_data['store'].email}")
        title.setStyleSheet("font-size: 18px; color: #ffca28; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Filas de Cuentas (One row per Account)
        accounts = store_data.get('accounts', [])
        for game_account in accounts:
            row_widget = AlchemyRow(game_account, controller)
            # Conectar señal de edición
            row_widget.editRequested.connect(view_parent.on_edit_account_requested)
            layout.addWidget(row_widget)

class AlchemyView(QWidget):
    # Señal para volver al inicio
    backRequested = pyqtSignal()

    def __init__(self, server_id, server_name):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.controller = AlchemyController()
        # Cacheamos los datos
        self.data = [] 
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT PANEL (Emails) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        header_left = QHBoxLayout()
        header_left.setSpacing(10)
        
        btn_back = QPushButton("←")
        btn_back.setFixedWidth(40)
        btn_back.setFixedHeight(30)
        btn_back.clicked.connect(self.backRequested.emit)
        btn_back.setStyleSheet("""
            QPushButton { 
                background-color: #263238; color: #b0bec5; 
                border: 1px solid #37474f; border-radius: 4px; font-weight: bold; font-size: 16px;
            }
            QPushButton:hover { background-color: #37474f; color: white; }
        """)
        
        left_title = QLabel(f"{self.server_name}")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d4af37;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Botón Crear Email
        btn_add_email = QPushButton("Agregar Correo") 
        btn_add_email.setFixedWidth(140)
        btn_add_email.setFixedHeight(30)
        btn_add_email.setToolTip("Crear Nuevo Correo")
        btn_add_email.clicked.connect(self.prompt_add_email)
        btn_add_email.setStyleSheet("""
            QPushButton { 
                background-color: #1565c0; 
                color: white; 
                border: 1px solid #1e88e5; 
                border-radius: 4px; 
                font-weight: bold; 
                font-size: 13px;
                padding: 5px;
            }
            QPushButton:hover { background-color: #1e88e5; }
        """)
        
        # Header layout
        header_left.addWidget(btn_back)
        header_left.addWidget(left_title, 1)
        
        # Sub-layout para el botón de agregar abajo o al lado? 
        # El usuario lo quiere ver bien. Pongamoslo debajo del título en vertical?
        # No, el header es horizontal. Pongamoslo en una toolbar debajo del header.
        
        left_layout.addLayout(header_left)
        
        # Toolbar para acciones de correo
        email_toolbar = QHBoxLayout()
        email_toolbar.addWidget(btn_add_email)
        email_toolbar.addStretch()
        left_layout.addLayout(email_toolbar)
        
        self.store_list = QListWidget()
        self.store_list.setStyleSheet("""
            QListWidget {
                background-color: #263238; border: 1px solid #37474f; color: #b0bec5; font-size: 13px;
            }
            QListWidget::item { padding: 10px; }
            QListWidget::item:selected { background-color: #00bcd4; color: white; }
        """)
        self.store_list.itemClicked.connect(self.on_store_selected)
        left_layout.addWidget(self.store_list)
        
        # --- RIGHT PANEL (Accounts) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # Header Right
        header_right = QHBoxLayout()
        self.lbl_right_title = QLabel("Seleccione un Correo")
        self.lbl_right_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #eceff1;")
        
        # Botón Crear Cuenta (habilitado solo al seleccionar correo)
        self.btn_add_account = QPushButton("👤+ Crear Cuenta")
        self.btn_add_account.setFixedHeight(30)
        self.btn_add_account.setVisible(False) # Oculto hasta seleccionar
        self.btn_add_account.clicked.connect(self.prompt_add_game_account)
        self.btn_add_account.setStyleSheet("""
            QPushButton { 
                background-color: #2e7d32; color: white; border: none; 
                border-radius: 4px; font-weight: bold; font-size: 14px; padding: 0 10px;
            }
            QPushButton:hover { background-color: #388e3c; }
        """)

        header_right.addWidget(self.lbl_right_title)
        header_right.addStretch()
        header_right.addWidget(self.btn_add_account)
        right_layout.addLayout(header_right)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #102027; }")
        
        self.details_container = QWidget()
        self.details_container.setStyleSheet("background-color: #102027;")
        self.details_layout = QVBoxLayout()
        self.details_container.setLayout(self.details_layout)
        
        self.scroll.setWidget(self.details_container)
        right_layout.addWidget(self.scroll)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)
        
        self.load_data()

    def load_data(self, preserve_selection=None):
        self.data = self.controller.get_alchemy_dashboard_data(self.server_id)
        self.store_list.clear() # Limpia lista visual
        self.clear_details()
        self.lbl_right_title.setText("Seleccione un Correo")
        self.btn_add_account.setVisible(False)
        self.selected_email = None
        
        # Obtener lista de emails únicos (pueden venir duplicados si la query no agrupa bien, pero controller ya agrupa)
        # La data del controller ya es una lista de diccionarios agrupados por store.
        for entry in self.data:
             self.store_list.addItem(entry['store'].email)
        
        if preserve_selection:
            items = self.store_list.findItems(preserve_selection, Qt.MatchFlag.MatchExactly)
            if items:
                self.store_list.setCurrentItem(items[0])
                self.on_store_selected(items[0])

    def on_store_selected(self, item):
        email = item.text()
        self.selected_email = email
        self.lbl_right_title.setText(f"Cuentas en: {email}")
        self.btn_add_account.setVisible(True)
        
        selected_store_data = next((d for d in self.data if d['store'].email == email), None)
        
        if selected_store_data:
            self.clear_details()
            details = StoreDetailsWidget(selected_store_data, self.controller, self)
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
                 QMessageBox.warning(self, "Error", "No se pudo crear el correo (¿Ya existe?).")

    def prompt_add_game_account(self):
        if not self.selected_email: return
        
        from src.views.dialogs.account_dialog import AccountDialog
        
        dialog = AccountDialog(self, email=self.selected_email)
        dialog.txt_email.setReadOnly(True)
        
        if dialog.exec():
            _, username, pj_name, slots = dialog.get_data()
            
            if self.controller.create_game_account(self.server_id, username, slots, self.selected_email, pj_name):
                QMessageBox.information(self, "Éxito", f"Cuenta '{username}' agregada a '{self.selected_email}'.")
                self.load_data(preserve_selection=self.selected_email)
            else:
                QMessageBox.warning(self, "Error", "No se pudo crear la cuenta (¿Usuario duplicado?).")

    def on_edit_account_requested(self, game_account):
        # Para editar, necesitamos saber qué editar.
        # Por simplicidad ahora: Nombre Usuario, Slots. (Y nombre visual PJ?)
        # Recuperamos nombre visual del primer PJ
        first_char = game_account.characters[0] if game_account.characters else None
        current_pj_name = first_char.name.split('_')[0] if first_char else ""

        from src.views.dialogs.account_dialog import AccountDialog
        current_slots = len(game_account.characters)
        current_email = game_account.store_account.email
        
        dialog = AccountDialog(self, username=game_account.username, slots=current_slots, email=current_email, edit_mode=True)
        dialog.txt_pj_name.setText(current_pj_name)
        
        if dialog.exec():
            new_email, new_name, new_pj_name, new_slots = dialog.get_data()
            
            # TODO: Update logic needs to handle pj_name update too?
            # For now just basic account update
            if self.controller.update_game_account(game_account.id, new_name, new_slots, new_email):
                 QMessageBox.information(self, "Éxito", "Cuenta actualizada.")
                 self.load_data(preserve_selection=new_email)
            else:
                 QMessageBox.warning(self, "Error", "No se pudo actualizar.")

