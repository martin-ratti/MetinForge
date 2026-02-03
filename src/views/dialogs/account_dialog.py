from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QSpinBox, QDialogButtonBox

class AccountDialog(QDialog):
    def __init__(self, parent=None, username="", slots=5, email="", edit_mode=False):
        super().__init__(parent)
        self.setWindowTitle("Editar Cuenta" if edit_mode else "Nueva Cuenta")
        self.setWindowTitle("Editar Cuenta" if edit_mode else "Nueva Cuenta")
        # Quitamos tamaño fijo vertical para que se adapte al contenido
        # self.setFixedSize(350, 250) 
        self.setMinimumWidth(400) # Un poco más ancho
        self.setStyleSheet("""
            QDialog { background-color: #263238; color: #eceff1; }
            QLabel { color: #b0bec5; font-size: 14px; }
            QLineEdit, QSpinBox { 
                background-color: #37474f; 
                color: white; 
                border: 1px solid #546e7a; 
                padding: 5px; 
                border-radius: 4px;
            }
            QPushButton {
                background-color: #00bcd4; color: white; padding: 6px; border-radius: 4px; border: none; font-weight: bold;
            }
            QPushButton:hover { background-color: #26c6da; }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setMinimumWidth(350) # Ancho minimo para que no se vea apretado
        
        layout.setSpacing(15) # Mas espacio entre elementos
        layout.setContentsMargins(20, 20, 20, 20)

        # Estilo para inputs más grandes y claros
        input_style = """
            QLineEdit, QSpinBox {
                padding: 5px 8px; /* Padding vertical y horizontal */
                font-size: 14px;
                border: 1px solid #546e7a;
                border-radius: 4px;
                background-color: #37474f;
                color: #ffffff;
                min-height: 25px; /* Altura minima algo mayor */
                margin-top: 2px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #29b6f6;
                background-color: #455a64;
            }
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #cfd8dc;
                background: transparent; /* Quitar fondo negro si habia */
            }
        """
        self.setStyleSheet(input_style) # Aplicar estilo al dialogo entero para afectar labels tambien

        layout.addWidget(QLabel("Email de Tienda:"))
        self.txt_email = QLineEdit(email)
        # Ya hereda estilo, solo read-only visual si aplica
        layout.addWidget(self.txt_email)

        layout.addWidget(QLabel("Nombre de Cuenta:"))
        self.txt_name = QLineEdit(username)
        self.txt_name.setPlaceholderText("Ej: Fragmetin11_S")
        layout.addWidget(self.txt_name)

        layout.addWidget(QLabel("Nombre del Personaje:"))
        self.txt_pj_name = QLineEdit() 
        self.txt_pj_name.setPlaceholderText("Ej: Reynares")
        layout.addWidget(self.txt_pj_name)

        layout.addWidget(QLabel("Cantidad de Slots:"))
        self.spin_slots = QSpinBox()
        self.spin_slots.setRange(1, 10)
        self.spin_slots.setValue(slots)
        self.spin_slots.setFixedHeight(35) # Altura fija para el spinbox que a veces es rebelde
        layout.addWidget(self.spin_slots)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return self.txt_email.text().strip(), self.txt_name.text().strip(), self.txt_pj_name.text().strip(), self.spin_slots.value()
