from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from app.presentation.models.alchemy_model import AlchemyModel

class DailyGridDelegate(QStyledItemDelegate):
    """Delegado grafico para renderizar la grilla de dias."""
    
    CELL_SIZE = 22
    SPACING = 2
    
    def __init__(self, parent=None, total_days=30, controller=None, model=None):
        super().__init__(parent)
        self.total_days = total_days
        self.controller = controller
        self.color_pending = QColor("#2b2b2b")
        self.color_success = QColor("#d4af37")
        self.color_fail = QColor("#550000")
        self.border_pen = QPen(QColor("#5d4d2b"))
        self.text_pen = QPen(QColor("#ffffff"))

    def paint(self, painter, option, index):
        item_type = index.data(AlchemyModel.TypeRole)
        
        if item_type == "store" and index.column() == 3:
            painter.save()
            rect = option.rect
            painter.fillRect(rect, QColor("#102027"))
            
            start_x = rect.x()
            start_y = rect.y() + (rect.height() - self.CELL_SIZE) // 2
            current_x = start_x
            
            painter.setPen(QColor("#a0a0a0"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(8)
            painter.setFont(font)

            for day in range(1, self.total_days + 1):
                day_rect = QRect(current_x, start_y, self.CELL_SIZE, self.CELL_SIZE)
                painter.drawText(day_rect, Qt.AlignmentFlag.AlignCenter, str(day))
                current_x += self.CELL_SIZE + self.SPACING
            
            painter.restore()
            return

        if item_type != "account":
            super().paint(painter, option, index)
            return

        if index.column() != 3:
            super().paint(painter, option, index)
            return
            
        painter.save()
        
        grid_data = index.data(AlchemyModel.GridDataRole) or {}
        rect = option.rect
        
        start_x = rect.x()
        start_y = rect.y() + (rect.height() - self.CELL_SIZE) // 2
        current_x = start_x
        
        for day in range(1, self.total_days + 1):
            status = grid_data.get(day, 0)
            day_rect = QRect(current_x, start_y, self.CELL_SIZE, self.CELL_SIZE)
            
            bg_brush = QBrush(self.color_pending)
            text_str = ""
            
            if status == 1:
                bg_brush = QBrush(self.color_success)
                text_str = "✓"
                painter.setPen(QPen(Qt.GlobalColor.black))
            elif status == -1:
                bg_brush = QBrush(self.color_fail)
                text_str = "✕"
                painter.setPen(QPen(QColor("#ffcccc")))
            else:
                painter.setPen(self.border_pen)
            
            painter.setBrush(bg_brush)
            painter.drawRect(day_rect)
            
            painter.setPen(self.border_pen)
            painter.drawRect(day_rect)
            
            if text_str:
                painter.drawText(day_rect, Qt.AlignmentFlag.AlignCenter, text_str)
            
            painter.setPen(QColor("#707070"))
            font = painter.font()
            font.setPointSize(7)
            painter.setFont(font)
            
            year_rect = QRect(day_rect.x() + 2, day_rect.y() + 2, 15, 10)
            painter.drawText(year_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(day))
            
            current_x += self.CELL_SIZE + self.SPACING
            
        painter.restore()

    def sizeHint(self, option, index):
        if index.column() == 3:
            width = (self.CELL_SIZE + self.SPACING) * self.total_days
            return QSize(width, self.CELL_SIZE + 4)
        return super().sizeHint(option, index)

    def editorEvent(self, event, model, option, index):
        """Maneja clics para actualizar estado sin modo edicion."""
        if event.type() == event.Type.MouseButtonRelease:
            if index.column() == 3 and index.data(AlchemyModel.TypeRole) == "account":
                click_x = event.pos().x()
                rect = option.rect
                
                rel_x = click_x - rect.x()
                cell_total_width = self.CELL_SIZE + self.SPACING
                idx = rel_x // cell_total_width
                day = idx + 1
                
                if 1 <= day <= self.total_days:
                    account = index.data(AlchemyModel.RawDataRole)
                    if not account: return False

                    activity = getattr(account, 'current_event_activity', {})
                    current_status = activity.get(day, 0)
                    
                    # Validacion secuencial: no modificar dia N si dia N-1 no esta hecho
                    if day > 1:
                        prev_status = activity.get(day - 1, 0)
                        if prev_status == 0:
                            return True

                    # Toggle: 0 -> 1 -> -1 -> 0
                    new_status = 0
                    if current_status == 0: new_status = 1
                    elif current_status == 1: new_status = -1
                    else: new_status = 0
                    
                    if account.characters:
                        char_id = account.characters[0].id
                        if self.controller:
                            event_id = model._event_id
                            if event_id:
                                self.controller.update_daily_status(char_id, day, new_status, event_id)
                                model.update_daily_status(index, day, new_status)
                                
                    return True
                    
        return super().editorEvent(event, model, option, index)
