from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QPixmap, QColor, QPen, QBrush
import os
from app.utils.logger import logger

class FeatureCardButton(QPushButton):
    """Custom button with background image and hover effect"""
    
    def __init__(self, text, image_path):
        super().__init__(text)
        self.image_path = image_path
        self.is_hovered = False
        
        # Load image
        if os.path.exists(image_path):
            self.bg_image = QPixmap(image_path)
            logger.debug(f"Loaded image: {image_path}")
        else:
            self.bg_image = None
            logger.warning(f"Image not found: {image_path}")
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Make cards expand to fill available space
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(250, 400)
        
        # Base style
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(27, 29, 14, 0.85);
                color: #d4af37;
                font-size: 24px;
                font-weight: bold;
                border: 3px solid #5d4d2b;
                border-radius: 15px;
                padding: 20px;
            }
            QPushButton:hover {
                background-color: rgba(45, 29, 15, 0.95);
                border: 3px solid #d4af37;
                color: #ffffff;
            }
        """)
    
    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        # Draw image FIRST (behind everything)
        if self.bg_image and not self.bg_image.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Calculate position to center image
            img_width = self.bg_image.width()
            img_height = self.bg_image.height()
            
            # Scale to fit button while maintaining aspect ratio
            scale_factor = min(self.width() / img_width, self.height() / img_height) * 0.5
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)
            
            # Center the image
            x = (self.width() - new_width) // 2
            y = (self.height() - new_height) // 2
            
            # Set opacity based on hover state
            if self.is_hovered:
                painter.setOpacity(1.0)  # Full color on hover
            else:
                painter.setOpacity(0.45)  # More visible opacity when not hovering
            
            # Draw the scaled image
            scaled_pixmap = self.bg_image.scaled(
                new_width, new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()
        
        # Then draw button background and text on TOP
        super().paintEvent(event)

