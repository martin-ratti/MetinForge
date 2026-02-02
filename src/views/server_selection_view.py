from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QFrame
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

    def __init__(self):
        super().__init__()
        self.controller = AlchemyController()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        # Titulo
        title = QLabel("Selecciona un Servidor")
        title.setStyleSheet("font-size: 24px; color: #eceff1; font-weight: bold; margin-bottom: 30px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Grid de servidores
        grid_frame = QFrame()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        grid_frame.setLayout(grid_layout)
        
        servers = self.controller.get_servers()
        
        if not servers:
            no_server_lbl = QLabel("No hay servidores disponibles.\nAgrega uno en la base de datos.")
            no_server_lbl.setStyleSheet("color: #b0bec5; font-size: 14px;")
            no_server_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_server_lbl)
        else:
            # Crear tarjetas
            row = 0
            col = 0
            max_cols = 3
            
            for srv in servers:
                card = ServerCard(srv)
                # Conectar click
                # Usamos lambda con default arg para el closure
                card.clicked.connect(lambda checked, s=srv: self.on_server_click(s))
                
                grid_layout.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            layout.addWidget(grid_frame)

    def on_server_click(self, server):
        self.serverSelected.emit(server.id, server.name)
