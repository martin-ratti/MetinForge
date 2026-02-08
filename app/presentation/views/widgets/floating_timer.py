from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QInputDialog, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QMouseEvent
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.utils.config import Config
from app.domain.models import TimerRecord

class FloatingTimer(QWidget):
    def __init__(self):
        super().__init__()
        
        # Database setup
        engine = create_engine(Config.get_db_url())
        self.Session = sessionmaker(bind=engine)
        
        # Timer state
        self.elapsed_ms = 0  # Track milliseconds
        self.is_running = False
        
        # QTimer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        
        # Dragging
        self.dragging = False
        self.drag_position = QPoint()
        
        self.init_ui()
        
    def init_ui(self):
        # Make window frameless and stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # Fixed size
        self.setFixedSize(270, 120)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.setLayout(layout)
        
        # Display - single label for simplicity
        self.time_label = QLabel("00:00:00.00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #d4af37;
                font-size: 22px;
                font-weight: bold;
                font-family: 'Consolas', 'Monaco', monospace;
                border: 2px solid #5d4d2b;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        
        layout.addWidget(self.time_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)
        
        btn_style = """
            QPushButton {
                background-color: #2b1d0e;
                color: #d4af37;
                border: 2px solid #5d4d2b;
                font-weight: bold;
                font-size: 12px;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #3d2b1f;
                border: 2px solid #d4af37;
            }
            QPushButton:pressed {
                background-color: #d4af37;
                color: #000;
            }
        """
        
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(50, 30)
        self.btn_play.setStyleSheet(btn_style)
        self.btn_play.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.btn_play)
        
        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setFixedSize(50, 30)
        self.btn_stop.setStyleSheet(btn_style)
        self.btn_stop.clicked.connect(self.stop_timer)
        controls_layout.addWidget(self.btn_stop)
        
        self.btn_history = QPushButton("📜")
        self.btn_history.setFixedSize(50, 30)
        self.btn_history.setStyleSheet(btn_style)
        self.btn_history.clicked.connect(self.show_history)
        controls_layout.addWidget(self.btn_history)
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(50, 30)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #550000;
                color: #ffcccc;
                border: 2px solid #800000;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #800000;
                border: 2px solid #ff4444;
            }
        """)
        self.btn_close.clicked.connect(self.close)
        controls_layout.addWidget(self.btn_close)
        
        layout.addLayout(controls_layout)
        
        # Overall widget style
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 3px solid #d4af37;
                border-radius: 10px;
            }
        """)
        
        # Position at top-right
        self.move_to_top_right()
    
    def move_to_top_right(self):
        screen = self.screen().geometry()
        self.move(screen.width() - self.width() - 20, 20)
    
    def toggle_play_pause(self):
        if self.is_running:
            # Pause
            self.timer.stop()
            self.is_running = False
            self.btn_play.setText("▶")
        else:
            # Play
            self.timer.start(10)  # Update every 10 milliseconds
            self.is_running = True
            self.btn_play.setText("⏸")
    
    def stop_timer(self):
        if self.elapsed_ms == 0:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Cronómetro")
            msg_box.setText("El cronómetro está en 00:00:00.00")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2b2b2b;
                }
                QMessageBox QLabel {
                    color: #e0e0e0;
                    font-size: 14px;
                }
                QMessageBox QPushButton {
                    background-color: #2b1d0e;
                    color: #d4af37;
                    border: 2px solid #5d4d2b;
                    font-weight: bold;
                    padding: 8px 20px;
                    border-radius: 5px;
                    min-width: 80px;
                }
            """)
            msg_box.exec()
            return
        
        # Stop timer
        self.timer.stop()
        self.is_running = False
        self.btn_play.setText("▶")
        
        # Ask for name with custom dialog
        from app.presentation.views.dialogs.save_record_dialog import SaveRecordDialog
        
        # Format time without HTML for dialog
        total_seconds = self.elapsed_ms // 1000
        ms = (self.elapsed_ms % 1000) // 10
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:02d}"
        
        dialog = SaveRecordDialog(time_str, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name()
            if name:
                self.save_record(name)
                # Custom styled message box
                self.show_success_message(f"Registro '{name}' guardado exitosamente.")
        
        # Reset
        self.elapsed_ms = 0
        self.update_display()
    
    def show_success_message(self, message):
        """Show a styled success message"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Guardado")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply Metin2 theme
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
        
        msg_box.exec()
    
    def save_record(self, name):
        session = self.Session()
        try:
            record = TimerRecord(
                name=name,
                elapsed_seconds=self.elapsed_ms // 1000  # Convert ms to seconds
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error saving timer record: {e}")
        finally:
            session.close()
    
    def update_display(self):
        self.elapsed_ms += 10  # Increment by 10ms
        total_seconds = self.elapsed_ms // 1000
        ms = (self.elapsed_ms % 1000) // 10  # Get centiseconds (10ms units)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        # Update single label
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:02d}")
    
    def format_time(self, milliseconds):
        total_seconds = milliseconds // 1000
        ms = (milliseconds % 1000) // 10  # Get centiseconds (10ms units)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}<span style='font-size: 16px;'>.{ms:02d}</span>"
    
    def show_history(self):
        from app.presentation.views.timer_history_view import TimerHistoryView
        # Keep reference to prevent garbage collection
        self.history_window = TimerHistoryView()
        self.history_window.show()
    
    # Drag and drop
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
