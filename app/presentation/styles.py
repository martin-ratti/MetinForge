from PyQt6.QtGui import QColor

class AppColors:
    # Grid Status
    SUCCESS = QColor("#d4af37")  # Gold
    FAIL = QColor("#550000")     # Dark Red
    PENDING = QColor("#2b2b2b")
    BORDER = QColor("#5d4d2b")
    
    # UI Elements
    HEADER_BG = QColor("#102027")
    TEXT_PRIMARY = QColor("#d4af37") # Gold
    TEXT_SECONDARY = QColor("#b0bec5") # Grey
    
    # Progress
    PROG_COMPLETED = QColor("#4fc3f7")
    PROG_FAILED = QColor("#ef5350")
    PROG_PENDING = QColor("#78909c")
    PROG_TOTAL = QColor("#b0bec5")
    
    # Selection
    SELECTION_BG = QColor("#263238")

class AppDims:
    # Fishing / Tombola Grid
    CELL_SIZE = 18
    SPACING = 2
    MONTH_SPACING = 6

class AppStyles:
    BUTTON_BACK = """
        QPushButton {
            background-color: #550000;
            border: 2px solid #800000;
            color: #ffcccc;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:hover { background-color: #800000; }
    """
    
    BUTTON_IMPORT = """
        QPushButton {
            background-color: #2e7d32;
            color: white;
            border: 1px solid #1b5e20;
            border-radius: 4px;
            padding: 8px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover { background-color: #388e3c; }
    """
    
    FRAME_PROGRESS = """
        QFrame {
            background-color: #102027;
            border: 1px solid #37474f;
            border-radius: 8px;
        }
        QLabel {
            border: none;
            background: transparent;
        }
    """
    
    LABEL_TITLE = "font-size: 16px; font-weight: bold; color: #d4af37;"
    LABEL_SUBTITLE = "font-size: 14px; font-weight: bold; color: #d4af37;"
    
    LABEL_BADGE = """
        font-size: 14px; 
        font-weight: bold; 
        color: #d4af37; 
        background-color: #263238; 
        border: 1px solid #d4af37; 
        border-radius: 4px; 
        padding: 4px 8px;
    """
    
    COMBO_BOX = """
        padding: 5px; 
        background-color: #263238; 
        color: white; 
        border: 1px solid #546e7a; 
        border-radius: 4px;
    """
    
    BUTTON_ACTION = """
        QPushButton { 
            background-color: #1565c0; 
            color: white; 
            border: 1px solid #1e88e5; 
            border-radius: 4px; 
            font-weight: bold; 
        }
    """
    
    BUTTON_SECONDARY = """
        QPushButton { 
            background-color: #455a64; 
            color: white; 
            border: 1px solid #607d8b; 
            border-radius: 4px; 
            font-weight: bold; 
        }
    """
    
    BUTTON_ACCENT = """
        QPushButton {
            background-color: #f57f17; 
            color: white; 
            border-radius: 4px; 
            font-weight: bold; 
            padding: 5px 10px;
        }
    """
