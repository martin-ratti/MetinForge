from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QDialog, QTimeEdit, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPoint, QTime
from PyQt6.QtGui import QMouseEvent, QColor
import winsound
import os

class SingleTimerWidget(QFrame):
    def __init__(self, parent_manager, initial_seconds=300):
        super().__init__()
        self.manager = parent_manager
        self.initial_duration_ms = initial_seconds * 1000
        self.remaining_ms = self.initial_duration_ms
        self.is_running = False
        self.blink_state = False
        
        # Timer for countdown
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        
        # Timer for blinking alarm
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_action)
        self.blink_timer.setInterval(500) # Blink every 500ms
        
        self.init_ui()
        self.render_time()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #5d4d2b;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # Time Display
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("""
            background-color: transparent;
            color: #d4af37;
            font-size: 20px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            border: none;
        """)
        layout.addWidget(self.time_label)
        
        # Controls
        btn_style = """
            QPushButton {
                background-color: #2b1d0e;
                color: #d4af37;
                border: 1px solid #5d4d2b;
                font-weight: bold;
                font-size: 12px;
                border-radius: 3px;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background-color: #3d2b1f;
                border: 1px solid #d4af37;
            }
        """
        
        # Reload Button
        self.btn_reload = QPushButton("🔄")
        self.btn_reload.setFixedSize(30, 25)
        self.btn_reload.setStyleSheet(btn_style)
        self.btn_reload.clicked.connect(self.reload_timer)
        layout.addWidget(self.btn_reload)
        
        # Play/Pause
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(30, 25)
        self.btn_play.setStyleSheet(btn_style)
        self.btn_play.clicked.connect(self.toggle_play_pause)
        layout.addWidget(self.btn_play)
        
        # Config (Set Time)
        self.btn_config = QPushButton("⚙️")
        self.btn_config.setFixedSize(30, 25)
        self.btn_config.setStyleSheet(btn_style)
        self.btn_config.clicked.connect(self.set_time)
        layout.addWidget(self.btn_config)
        
        # Delete
        self.btn_delete = QPushButton("✖") # Standard "Heavy Multiplication X" or just "X"
        self.btn_delete.setFixedSize(30, 25)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #2b1d0e;
                color: #ff8a80;
                border: 1px solid #5d4d2b;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3e2723;
                border: 1px solid #ff5252;
                color: #ff5252;
            }
        """)
        self.btn_delete.clicked.connect(self.delete_timer)
        layout.addWidget(self.btn_delete)

    def set_time(self):
        if self.is_running:
            self.toggle_play_pause()
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar")
        dialog.setFixedSize(250, 120)
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setStyleSheet("background-color: #2b2b2b; border: 2px solid #d4af37;")
        
        d_layout = QVBoxLayout()
        dialog.setLayout(d_layout)
        
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm:ss")
        # Calc current set time
        secondsTotal = self.initial_duration_ms // 1000
        h = secondsTotal // 3600
        m = (secondsTotal % 3600) // 60
        s = secondsTotal % 60
        time_edit.setTime(QTime(h, m, s))
        time_edit.setStyleSheet("background-color: #1a1a1a; color: #d4af37; font-size: 20px; border: 1px solid #5d4d2b;")
        d_layout.addWidget(time_edit)
        
        btn_ok = QPushButton("Aplicar")
        btn_ok.setStyleSheet("background-color: #2b1d0e; color: #d4af37; border: 1px solid #5d4d2b; padding: 5px;")
        btn_ok.clicked.connect(dialog.accept)
        d_layout.addWidget(btn_ok)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            t = time_edit.time()
            total_seconds = t.hour() * 3600 + t.minute() * 60 + t.second()
            self.initial_duration_ms = total_seconds * 1000
            self.remaining_ms = self.initial_duration_ms
            self.stop_alarm() # Stop any alarm if currently ringing
            self.render_time()

    def toggle_play_pause(self):
        if self.remaining_ms <= 0 and not self.blink_timer.isActive():
            # If finished but not alarming (stopped manually at 0?), restart
            self.reload_timer()
            return

        if self.blink_timer.isActive():
            # If alarming, stop alarm
            self.stop_alarm()
            return

        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.btn_play.setText("▶")
        else:
            self.timer.start(100) # Update every 100ms is enough for seconds
            self.is_running = True
            self.btn_play.setText("⏸")

    def reload_timer(self):
        self.stop_alarm()
        self.timer.stop()
        self.is_running = False
        self.remaining_ms = self.initial_duration_ms
        self.render_time()
        self.toggle_play_pause() # Auto start

    def update_display(self):
        self.remaining_ms -= 100
        if self.remaining_ms <= 0:
            self.remaining_ms = 0
            self.timer.stop()
            self.is_running = False
            self.render_time()
            self.start_alarm()
        else:
            self.render_time()

    def render_time(self):
        total_seconds = (self.remaining_ms + 99) // 1000 # Ceil for display
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")

    def start_alarm(self):
        self.blink_timer.start()
        # Play sound loop logic handled in blink_action to sync or just once
        # User wants annoying alarm? Or just beep?
        # Logic: Beep every blink
        self.blink_action()

    def stop_alarm(self):
        self.blink_timer.stop()
        self.blink_state = False
        
        # STOP SOUND immediately
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except:
            pass

        # Reset style
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #5d4d2b;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)

    def blink_action(self):
        self.blink_state = not self.blink_state
        if self.blink_state:
            # Alarm State
            self.setStyleSheet("""
                QFrame {
                    background-color: #b71c1c; /* RED ALERT */
                    border: 2px solid #ff5252;
                    border-radius: 5px;
                    margin-bottom: 5px;
                }
            """)
            
            # Sound Logic
            try:
                # Resolve path relative to this file to be robust
                base_dir = os.path.dirname(os.path.abspath(__file__)) # app/views/widgets
                sound_path = os.path.join(base_dir, "..", "..", "..", "app", "assets", "sounds", "alarm.wav")
                sound_path = os.path.abspath(sound_path)
                
                if os.path.exists(sound_path):
                    # winsound.PlaySound handles WAV files well on Windows
                    # SND_FILENAME | SND_ASYNC (1 | 8) | SND_LOOP (8) to loop while alarming
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
                else:
                    print(f"Sound not found at: {sound_path}")
                    # 2. Fallback to System Beep (Hardware/Driver dependent)
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception as e:
                print(f"Error playing sound: {e}")
        else:
            # Normal State (Flash)
            self.setStyleSheet("""
                QFrame {
                    background-color: #1a1a1a;
                    border: 1px solid #5d4d2b;
                    border-radius: 5px;
                }
            """)

    def delete_timer(self):
        self.stop_alarm()
        self.timer.stop()
        self.manager.remove_timer(self)


class FloatingCountdown(QWidget):
    def __init__(self):
        super().__init__()
        self.timers = []
        self.dragging = False
        self.drag_position = QPoint()
        
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self.setFixedSize(300, 400) # Taller for list
        
        # Main Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        # Header (Drag Area)
        header = QHBoxLayout()
        lbl_title = QLabel("Temporizadores")
        lbl_title.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 14px;")
        header.addWidget(lbl_title)
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(25, 25)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("""
            QPushButton { background-color: transparent; color: #ff8a80; font-weight: bold; font-size: 16px; border: none; }
            QPushButton:hover { color: red; }
        """)
        header.addWidget(btn_close)
        layout.addLayout(header)
        
        # Scroll Area for Timers
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 5px; background: #1a1a1a; }
            QScrollBar::handle:vertical { background: #5d4d2b; border-radius: 2px; }
        """)
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.timers_layout = QVBoxLayout()
        self.timers_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.timers_layout.setSpacing(5)
        self.container.setLayout(self.timers_layout)
        
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        
        # Add Button
        self.btn_add = QPushButton("➕ Agregar Temporizador")
        self.btn_add.setFixedHeight(35)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #2b1d0e;
                color: #d4af37;
                border: 1px solid #5d4d2b;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3d2b1f;
                border: 1px solid #ffcc00;
            }
        """)
        self.btn_add.clicked.connect(self.add_timer)
        layout.addWidget(self.btn_add)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 2px solid #d4af37;
                border-radius: 10px;
            }
        """)
        
        self.move_to_top_right()
        
        # Add initial timer
        self.add_timer()

    def move_to_top_right(self):
        screen = self.screen().geometry()
        self.move(screen.width() - self.width() - 20, 150)

    def add_timer(self):
        timer_widget = SingleTimerWidget(self)
        self.timers.append(timer_widget)
        self.timers_layout.addWidget(timer_widget)

    def remove_timer(self, timer_widget):
        if timer_widget in self.timers:
            self.timers.remove(timer_widget)
            timer_widget.deleteLater()

    # Dragging logic
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Only drag if clicking header area roughly (top 40px)
            if event.position().y() < 40:
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
