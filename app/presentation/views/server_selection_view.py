from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QFrame, QInputDialog, QMessageBox, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from app.application.services.alchemy_service import AlchemyService

class ServerCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, server, controller):
        super().__init__()
        self.server = server
        self.controller = controller
        self.controller = controller
        # Aumentamos tamaño para que respire mejor
        self.setFixedSize(280, 180) 
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Styles - Metin2 Palette
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a; 
                border: 2px solid #5d4d2b; 
                border-radius: 12px;
            }
            QFrame:hover {
                border: 2px solid #d4af37;
                background-color: #2b1d0e;
            }
            QLabel {
                color: #d4af37;
                font-size: 22px;
                font-weight: bold;
                border: none;
                background-color: transparent;
            }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(15, 20, 15, 20)
        
        # 1. Nombre Del Servidor
        lbl_name = QLabel(server.name.upper())
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_name)
        
        layout.addStretch()
        
        # 2. Toggle Buttons Row
        toggles_layout = QHBoxLayout()
        toggles_layout.setSpacing(10)
        toggles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Botones un poco más grandes y estilizados
        self.btn_daily = self.create_toggle("💎", server.has_dailies, "dailies")
        self.btn_fish = self.create_toggle("🐟", server.has_fishing, "fishing")
        self.btn_tombola = self.create_toggle("🎰", server.has_tombola, "tombola")
        
        toggles_layout.addWidget(self.btn_daily)
        toggles_layout.addWidget(self.btn_fish)
        toggles_layout.addWidget(self.btn_tombola)
        
        layout.addLayout(toggles_layout)
        layout.addSpacing(10)
        
    def create_toggle(self, icon, checked, feature_key):
        btn = QPushButton(icon)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setFixedSize(50, 50) # Más grandes
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Definimos los estilos aquí para poder pasarlos y swapearlos
        # Estilo Base
        base_style = """
            QPushButton {
                font-size: 24px;
                border-radius: 8px;
                margin: 0px;
            }
        """
        
        # Estilo Activo (Dorado Brillante)
        active_style = """
            background-color: #d4af37;
            border: 3px solid #ffcc00;
            color: #000;
            font-weight: bold;
        """
        
        # Estilo Inactivo (Muy Oscuro)
        inactive_style = """
            background-color: #0d0d0d;
            border: 2px solid #2b2b2b;
            color: #333;
        """
        
        # Aplicar inicial
        btn.setStyleSheet(base_style + (active_style if checked else inactive_style))
        
        # Connect logic
        btn.toggled.connect(lambda state: self.on_toggle(btn, state, feature_key, base_style, active_style, inactive_style))
        return btn

    def on_toggle(self, btn, state, feature, base, active, inactive):
        # Update UI
        btn.setStyleSheet(base + (active if state else inactive))
        
        # Update DB
        self.controller.update_server_feature(self.server.id, feature, state)

    def mousePressEvent(self, event):
        # Detectar si el click fue en el frame principal (para seleccionar server)
        # Los botones de toggle capturan su propio click, asi que si llegamos aqui es el fondo/nombre
        self.clicked.emit()

class ServerSelectionView(QWidget):
    # Señal que emite el ID del servidor seleccionado
    serverSelected = pyqtSignal(int, str) # id, name
    backRequested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.controller = AlchemyService()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Alineamos arriba
        self.setLayout(layout)

        # Header con Botones
        header_layout = QGridLayout()
        
        # Botón Volver
        btn_back = QPushButton("← Volver")
        btn_back.setStyleSheet("""
            QPushButton {
                 background-color: transparent; color: #b0bec5; 
                 font-size: 14px; border: none; text-align: left;
            }
            QPushButton:hover { color: white; }
        """)
        btn_back.clicked.connect(self.backRequested.emit)
        
        # Titulo
        title = QLabel("Selecciona un Servidor")
        title.setStyleSheet("font-size: 24px; color: #d4af37; font-weight: bold;") # Gold
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Botón Agregar
        btn_add = QPushButton("➕ Agregar")
        btn_add.setFixedWidth(100)
        btn_add.clicked.connect(self.add_server)
        
        header_layout.addWidget(btn_back, 0, 0)
        header_layout.addWidget(title, 0, 1)
        header_layout.addWidget(btn_add, 0, 2)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Grid de servidores
        self.grid_frame = QFrame()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.grid_frame.setLayout(self.grid_layout)
        layout.addWidget(self.grid_frame)
        layout.addStretch()
        
        self.load_servers()

    def load_servers(self):
        # Limpiar grid actual
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        servers = self.controller.get_servers()
        
        if not servers:
            no_server_lbl = QLabel("No hay servidores disponibles.")
            no_server_lbl.setStyleSheet("color: #b0bec5; font-size: 14px;")
            no_server_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(no_server_lbl, 0, 0)
        else:
            # Crear tarjetas
            row = 0
            col = 0
            max_cols = 3
            
            for srv in servers:
                card = ServerCard(srv, self.controller)
                # Conectar click
                card.clicked.connect(lambda s=srv: self.on_server_click(s))
                
                self.grid_layout.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def add_server(self):
        # Dialogo custom para pedir nombre y flags
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QCheckBox, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Servidor")
        dialog.setFixedWidth(300)
        dialog.setStyleSheet("background-color: #1a1a1a; color: #d4af37; border: 2px solid #5d4d2b;")
        
        d_layout = QVBoxLayout()
        dialog.setLayout(d_layout)
        
        d_layout.addWidget(QLabel("Nombre del Servidor:"))
        txt_name = QLineEdit()
        txt_name.setStyleSheet("padding: 5px; background-color: #2b2b2b; border: 1px solid #5d4d2b; color: #e0e0e0;")
        d_layout.addWidget(txt_name)
        
        d_layout.addWidget(QLabel("Funcionalidades:"))
        chk_dailies = QCheckBox("💎 Diarias (Alquimia)")
        chk_dailies.setChecked(True)
        d_layout.addWidget(chk_dailies)
        
        chk_fishing = QCheckBox("🐟 Pesca")
        chk_fishing.setChecked(True)
        d_layout.addWidget(chk_fishing)
        
        chk_tombola = QCheckBox("🎰 Tómbola")
        chk_tombola.setChecked(True)
        d_layout.addWidget(chk_tombola)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        d_layout.addWidget(buttons)
        
        if dialog.exec():
            name = txt_name.text().strip()
            if not name: return
            
            flags = {
                'dailies': chk_dailies.isChecked(),
                'fishing': chk_fishing.isChecked(),
                'tombola': chk_tombola.isChecked()
            }
            
            if self.controller.create_server(name, flags):
                QMessageBox.information(self, "Éxito", f"Servidor '{name}' creado.")
                self.load_servers()
            else:
                 QMessageBox.warning(self, "Error", "No se pudo crear (¿Nombre duplicado?).")

    def on_server_click(self, server):
        self.serverSelected.emit(server.id, server.name)
