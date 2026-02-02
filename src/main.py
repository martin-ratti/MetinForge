import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from qt_material import apply_stylesheet

# Importación ABSOLUTA (La forma correcta)
# Importación ABSOLUTA (La forma correcta)
from src.views.alchemy_view import AlchemyView
from src.views.server_selection_view import ServerSelectionView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MetinForge Manager v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        self.show_server_selection()
    
    def show_server_selection(self):
        self.selection_view = ServerSelectionView()
        self.selection_view.serverSelected.connect(self.show_alchemy)
        self.setCentralWidget(self.selection_view)
        
    def show_alchemy(self, server_id, server_name):
        self.alchemy_view = AlchemyView(server_id, server_name)
        self.alchemy_view.backRequested.connect(self.show_server_selection)
        self.setCentralWidget(self.alchemy_view)

def main():
    app = QApplication(sys.argv)
    
    # Aplicar tema oscuro (Cyan y Azul oscuro)
    apply_stylesheet(app, theme='dark_cyan.xml')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
