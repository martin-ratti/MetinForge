from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

class FeatureSelectionView(QWidget):
    featureSelected = pyqtSignal(str) # "dailies", "fishing", "tombola"
    backRequested = pyqtSignal()

    def __init__(self, server_name, flags):
        super().__init__()
        self.flags = flags # {'dailies': bool, 'fishing': bool, 'tombola': bool}
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header simple con botón atrás
        # Opcional, pero util para volver a seleccionar servidor
        
        # Estilo de botones gigantes - Metin2
        btn_style = """
            QPushButton {
                background-color: #2b1d0e;
                color: #d4af37;
                font-size: 24px;
                font-weight: bold;
                border: 2px solid #5d4d2b;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: #3d2b1f;
                border: 2px solid #d4af37;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #d4af37;
                color: #000000;
            }
        """
        
        # Boton Darias
        if self.flags.get('has_dailies', True):
            btn_dailies = QPushButton("Diarias (Alquimia, Cors)")
            # Asumimos que QSizePolicy ya está importado arriba o lo importamos aquí correctamente
            from PyQt6.QtWidgets import QSizePolicy
            btn_dailies.setSizePolicy(
                QSizePolicy.Policy.Expanding, 
                QSizePolicy.Policy.Expanding
            )
            btn_dailies.setStyleSheet(btn_style)
            btn_dailies.clicked.connect(lambda: self.featureSelected.emit("dailies"))
            layout.addWidget(btn_dailies)
            
        # Boton Pesca
        if self.flags.get('has_fishing', True):
            btn_fishing = QPushButton("Pesca")
            btn_fishing.setSizePolicy(
                 QSizePolicy.Policy.Expanding, 
                 QSizePolicy.Policy.Expanding
            )
            btn_fishing.setStyleSheet(btn_style)
            btn_fishing.clicked.connect(lambda: self.featureSelected.emit("fishing"))
            layout.addWidget(btn_fishing)

        # Boton Tombola
        if self.flags.get('has_tombola', True):
            btn_tombola = QPushButton("Tómbola")
            btn_tombola.setSizePolicy(
                 QSizePolicy.Policy.Expanding, 
                 QSizePolicy.Policy.Expanding
            )
            btn_tombola.setStyleSheet(btn_style)
            btn_tombola.clicked.connect(lambda: self.featureSelected.emit("tombola"))
            layout.addWidget(btn_tombola)

        # Boton Atras (Pequeño abajo o overlay? Por ahora abajo)
        btn_back = QPushButton("Volver a Selección de Servidor")
        btn_back.setFixedHeight(40)
        btn_back.setStyleSheet("background-color: #550000; border: 1px solid #800000; color: #ffcccc; font-weight: bold;")
        btn_back.clicked.connect(self.backRequested.emit)
        layout.addWidget(btn_back)
