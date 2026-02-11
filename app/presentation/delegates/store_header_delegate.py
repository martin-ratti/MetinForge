from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from app.presentation.models.alchemy_model import AlchemyModel

class StoreHeaderDelegate(QStyledItemDelegate):
    """
    Renderiza las filas de 'Tienda' como separadores visuales distintivos.
    Ocupa todo el ancho si es posible (en TreeView requiere span).
    """
    def paint(self, painter, option, index):
        if index.data(AlchemyModel.TypeRole) != "store":
            super().paint(painter, option, index)
            return

        painter.save()
        
        # Estilo Metin2 Separador
        bg_color = QColor("#102027")
        border_color = QColor("#37474f")
        text_color = QColor("#d4af37") # Gold
        
        rect = option.rect
        
        # Fondo
        painter.fillRect(rect, bg_color)
        
        # Borde inferior
        painter.setPen(QPen(border_color, 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        
        # Texto con icono
        # El texto ya viene formateado del modelo como "📧 email"
        text = index.data(Qt.ItemDataRole.DisplayRole)
        
        if text and index.column() == 0:
             painter.setPen(text_color)
             # Fuente Bold
             font = painter.font()
             font.setBold(True)
             font.setPointSize(10)
             painter.setFont(font)
             
             # Margen izquierdo
             text_rect = rect.adjusted(10, 0, 0, 0)
             painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
             
        # IMPORTANTE: Si estamos en columna 3 (Grid) o 4 (Cords), NO pintamos nada
        # para dejar que DailyGridDelegate o DefaultDelegate hagan su trabajo?
        # En QTreeView, si no hay span, se llama paint por cada celda.
        # Si queremos que parezca un header continuo en col 0-2:
        # Col 0, 1, 2 -> Pintamos Background y Borde.
        # Col 3 -> DailyGridDelegate pinta Background + Numeros.
        # Col 4 -> Delegate default pinta Background + Total?
        
        # Pero mi logica actual pinta Background en TODAS las celdas de tipo Store.
        # DailyGridDelegate YA pinta fondo en Col 3 para Store (ver paso anterior).
        # Asi que aqui debemos EVITAR pintar fondo en col 3.
        
        if index.column() == 3:
            painter.restore()
            return

        painter.restore()

    def sizeHint(self, option, index):
        return super().sizeHint(option, index)
