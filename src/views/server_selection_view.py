from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QFrame, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from src.controllers.alchemy_controller import AlchemyController

class ServerCard(QPushButton):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Estilo de la tarjeta
        self.setStyleSheet("""
            QPushButton {
                background-color: #263238; 
                border: 2px solid #37474f; 
                border-radius: 10px;
                color: #eceff1;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #37474f;
                border: 2px solid #00bcd4;
            }
            QPushButton:pressed {
                background-color: #00bcd4;
                color: #ffffff;
            }
        """)
        self.setText(server.name.upper())

class ServerSelectionView(QWidget):
    # Señal que emite el ID del servidor seleccionado
    serverSelected = pyqtSignal(int, str) # id, name
    backRequested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.controller = AlchemyController()
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
                card = ServerCard(srv)
                # Conectar click
                card.clicked.connect(lambda checked, s=srv: self.on_server_click(s))
                
                self.grid_layout.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def add_server(self):
        name, ok = QInputDialog.getText(self, "Agregar Servidor", "Nombre del Servidor:")
        if ok and name:
            name = name.strip()
            if not name:
                return
            
            if self.controller.create_server(name):
                QMessageBox.information(self, "Éxito", f"Servidor '{name}' creado.")
                self.load_servers()
            else:
                QMessageBox.warning(self, "Error", "No se pudo crear el servidor (quizás ya existe).")

    def on_server_click(self, server):
        self.serverSelected.emit(server.id, server.name)
