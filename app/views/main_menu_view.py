from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

class MainMenuView(QWidget):
    # Señales para navegación
    navigate_to_servers = pyqtSignal()
    open_timer = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #5d4d2b;
                border-radius: 10px;
                padding: 40px;
            }
        """)
        container_layout = QVBoxLayout()
        container_layout.setSpacing(20)
        container.setLayout(container_layout)

        title = QLabel("METIN FORGE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 48px; 
            font-weight: bold; 
            color: #d4af37; 
            font-family: 'Serif';
        """)
        container_layout.addWidget(title)
        
        subtitle = QLabel("Manager de Alquimia")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 18px; color: #a0a0a0; margin-bottom: 30px;")
        container_layout.addWidget(subtitle)

        btn_servers = self.create_main_button("GESTIONAR SERVIDORES")
        btn_servers.clicked.connect(self.navigate_to_servers.emit)
        
        btn_timer = self.create_main_button("⏱ CRONÓMETRO")
        btn_timer.clicked.connect(self.open_timer.emit)
        
        container_layout.addWidget(btn_servers)
        container_layout.addWidget(btn_timer)
        
        layout.addWidget(container)

    def create_main_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2b1d0e; /* Dark Brown/Goldish */
                color: #d4af37;
                border: 1px solid #7c6a36;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #3d2b1f;
                border: 1px solid #ffcc00;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #d4af37;
                color: #000000;
            }
        """)
        return btn
