from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.utils.config import Config
from app.models.models import TimerRecord

class TimerHistoryView(QWidget):
    def __init__(self):
        super().__init__()
        
        # Database setup
        engine = create_engine(Config.get_db_url())
        self.Session = sessionmaker(bind=engine)
        
        self.init_ui()
        self.load_history()
    
    def init_ui(self):
        self.setWindowTitle("Historial de Cronómetros")
        self.setGeometry(200, 200, 700, 500)
        
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        title = QLabel("📜 Historial de Cronómetros")
        title.setStyleSheet("""
            font-size: 20px;
            color: #d4af37;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Tiempo", "Fecha", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                border: 2px solid #5d4d2b;
                color: #e0e0e0;
                gridline-color: #3a3a3a;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3d2b1f;
                color: #d4af37;
            }
            QHeaderView::section {
                background-color: #2b1d0e;
                color: #d4af37;
                padding: 8px;
                border: 1px solid #5d4d2b;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)
        
        self.table.itemClicked.connect(self.on_table_item_clicked)
        
        btn_close = QPushButton("Cerrar")
        btn_close.setFixedHeight(35)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #550000;
                color: #ffcccc;
                border: 2px solid #800000;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #800000;
                border: 2px solid #ff4444;
            }
        """)
        layout.addWidget(btn_close)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
            }
        """)
    
    def load_history(self):
        session = self.Session()
        try:
            records = session.query(TimerRecord).order_by(TimerRecord.created_at.desc()).all()
            
            self.table.setRowCount(len(records))
            
            for row, record in enumerate(records):
                name_item = QTableWidgetItem(record.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 0, name_item)
                
                time_str = self.format_time(record.elapsed_seconds)
                time_item = QTableWidgetItem(time_str)
                time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, time_item)
                
                date_str = record.created_at.strftime("%Y-%m-%d %H:%M:%S")
                date_item = QTableWidgetItem(date_str)
                date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 2, date_item)
                
                action_item = QTableWidgetItem("🗑 Eliminar")
                action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                action_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_item.setForeground(Qt.GlobalColor.white)
                action_item.setBackground(Qt.GlobalColor.darkRed)
                action_item.setData(Qt.ItemDataRole.UserRole, record.id)
                self.table.setItem(row, 3, action_item)
        
        finally:
            session.close()
    
    def on_table_item_clicked(self, item):
        # Check if clicked on delete column (column 3)
        if item.column() == 3:
            record_id = item.data(Qt.ItemDataRole.UserRole)
            if record_id:
                self.delete_record(record_id)
    
    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def delete_record(self, record_id):
        # Custom styled question dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Eliminación")
        msg_box.setText("¿Estás seguro de que quieres eliminar este registro?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
            }
            QMessageBox QLabel {
                color: #e0e0e0;
                font-size: 14px;
                padding: 10px;
            }
            QMessageBox QPushButton {
                background-color: #2b1d0e;
                color: #d4af37;
                border: 2px solid #5d4d2b;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #3d2b1f;
                border: 2px solid #d4af37;
            }
        """)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            session = self.Session()
            try:
                record = session.query(TimerRecord).filter(TimerRecord.id == record_id).first()
                if record:
                    session.delete(record)
                    session.commit()
                    
                    # Success message
                    success_box = QMessageBox(self)
                    success_box.setWindowTitle("Eliminado")
                    success_box.setText("Registro eliminado exitosamente.")
                    success_box.setIcon(QMessageBox.Icon.Information)
                    success_box.setStyleSheet(msg_box.styleSheet())
                    success_box.exec()
                    
                    self.load_history()  # Refresh
            except Exception as e:
                session.rollback()
                
                # Error message
                error_box = QMessageBox(self)
                error_box.setWindowTitle("Error")
                error_box.setText(f"No se pudo eliminar: {e}")
                error_box.setIcon(QMessageBox.Icon.Warning)
                error_box.setStyleSheet(msg_box.styleSheet())
                error_box.exec()
            finally:
                session.close()
