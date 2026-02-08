from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from app.presentation.views.widgets.feature_card_button import FeatureCardButton
import os

class FeatureSelectionView(QWidget):
    featureSelected = pyqtSignal(str) # "dailies", "fishing", "tombola"
    backRequested = pyqtSignal()

    def __init__(self, server_name, flags):
        super().__init__()
        self.flags = flags # {'dailies': bool, 'fishing': bool, 'tombola': bool}
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Cards container (horizontal)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Get assets path
        # app/presentation/views/feature_selection_view.py -> ../../../.. -> root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        assets_dir = os.path.join(base_dir, "app", "presentation", "assets", "images")
        
        # Boton Diarias
        if self.flags.get('has_dailies', True):
            cor_image = os.path.join(assets_dir, "cor.png")
            btn_dailies = FeatureCardButton("Diarias\n(Alquimia, Cors)", cor_image)
            btn_dailies.clicked.connect(lambda: self.featureSelected.emit("dailies"))
            cards_layout.addWidget(btn_dailies)
            
        # Boton Pesca
        if self.flags.get('has_fishing', True):
            enchanted_image = os.path.join(assets_dir, "enchanted.png")
            btn_fishing = FeatureCardButton("Pesca", enchanted_image)
            btn_fishing.clicked.connect(lambda: self.featureSelected.emit("fishing"))
            cards_layout.addWidget(btn_fishing)

        # Boton Tombola
        if self.flags.get('has_tombola', True):
            talisman_image = os.path.join(assets_dir, "talisman.png")
            btn_tombola = FeatureCardButton("Tómbola", talisman_image)
            btn_tombola.clicked.connect(lambda: self.featureSelected.emit("tombola"))
            cards_layout.addWidget(btn_tombola)

        main_layout.addLayout(cards_layout)

        # Boton Atras
        btn_back = QPushButton("← Volver a Selección de Servidor")
        btn_back.setFixedHeight(50)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #550000; 
                border: 2px solid #800000; 
                color: #ffcccc; 
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #800000;
                border: 2px solid #ff4444;
            }
        """)
        btn_back.clicked.connect(self.backRequested.emit)
        main_layout.addWidget(btn_back)
