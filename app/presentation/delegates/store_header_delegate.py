from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from app.presentation.models.alchemy_model import AlchemyModel

class StoreHeaderDelegate(QStyledItemDelegate):
    """Renderiza las filas de 'Tienda' como separadores visuales."""
    
    def paint(self, painter, option, index):
        if index.data(AlchemyModel.TypeRole) != "store":
            super().paint(painter, option, index)
            return

        painter.save()
        
        bg_color = QColor("#102027")
        border_color = QColor("#37474f")
        text_color = QColor("#d4af37")
        
        rect = option.rect
        
        painter.fillRect(rect, bg_color)
        
        painter.setPen(QPen(border_color, 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        
        text = index.data(Qt.ItemDataRole.DisplayRole)
        
        if text and index.column() == 0:
             painter.setPen(text_color)
             font = painter.font()
             font.setBold(True)
             font.setPointSize(10)
             painter.setFont(font)
             
             text_rect = rect.adjusted(10, 0, 0, 0)
             painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)

        if index.column() == 3:
            painter.restore()
            return

        painter.restore()

    def sizeHint(self, option, index):
        return super().sizeHint(option, index)
