import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from qt_material import apply_stylesheet

# Importación ABSOLUTA (La forma correcta)
# Importación ABSOLUTA (La forma correcta)
from src.views.alchemy_view import AlchemyView
from src.views.server_selection_view import ServerSelectionView
from src.views.main_menu_view import MainMenuView
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MetinForge Manager v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        self.show_main_menu()
    
    def show_main_menu(self):
        self.menu_view = MainMenuView()
        self.menu_view.navigate_to_servers.connect(self.show_server_selection)
        self.setCentralWidget(self.menu_view)

    def show_server_selection(self):
        self.selection_view = ServerSelectionView()
        self.selection_view.serverSelected.connect(self.show_alchemy)
        self.selection_view.backRequested.connect(self.show_main_menu) # Nuevo: Volver al menú
        self.setCentralWidget(self.selection_view)
        
    def show_alchemy(self, server_id, server_name):
        self.alchemy_view = AlchemyView(server_id, server_name)
        self.alchemy_view.backRequested.connect(self.show_server_selection)
        self.setCentralWidget(self.alchemy_view)

def main():
    app = QApplication(sys.argv)
    
    # Cargar estilo Metin2
    style_path = os.path.join(os.path.dirname(__file__), "styles", "metin2.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print("⚠️ No se encontró el estilo Metin2, usando default.")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
