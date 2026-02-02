import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MetinForge Manager v0.1")
        self.setGeometry(100, 100, 1200, 800)
        
        label = QLabel("Bienvenido a MetinForge", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)

def main():
    app = QApplication(sys.argv)
    
    # Aqu� cargaremos los estilos m�s adelante
    # with open("assets/styles/dark_theme.qss", "r") as f:
    #    app.setStyleSheet(f.read())
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
