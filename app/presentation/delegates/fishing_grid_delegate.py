from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from app.presentation.models.fishing_model import FishingModel

class FishingGridDelegate(QStyledItemDelegate):
    """Delegate para renderizar la grilla anual de pesca (12 Meses x 4 Semanas) en una celda."""
    
    CELL_SIZE = 18
    SPACING = 2
    MONTH_SPACING = 6
    
    def __init__(self, parent=None, controller=None, model=None):
        super().__init__(parent)
        self.controller = controller
        self.model = model
        
        self.color_pending = QColor("#2b2b2b")
        self.color_success = QColor("#d4af37")  # Gold (like tombola)
        self.color_fail = QColor("#550000")     # Dark Red (like tombola)
        self.border_pen = QPen(QColor("#5d4d2b"))

    def paint(self, painter, option, index):
        if not index.isValid():
            return

        item_type = index.data(FishingModel.TypeRole)
        
        # Store header — draw month numbers
        if item_type == "store" and index.column() == 2:
            painter.save()
            rect = option.rect
            painter.fillRect(rect, QColor("#102027"))
            
            x = rect.x()
            y_center = rect.y() + (rect.height() - self.CELL_SIZE) // 2
            
            painter.setPen(QColor("#a0a0a0"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(8)
            painter.setFont(font)
            
            for m in range(1, 13):
                month_width = 4 * (self.CELL_SIZE + self.SPACING)
                month_rect = QRect(x, y_center, month_width, self.CELL_SIZE)
                painter.drawText(month_rect, Qt.AlignmentFlag.AlignCenter, str(m))
                x += month_width + self.MONTH_SPACING
            
            painter.restore()
            return

        # Account row — draw weekly grid
        if item_type == "account" and index.column() == 2:
            data = index.data(FishingModel.GridDataRole)
            if not data: data = {}
            
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            rect = option.rect
            y_center = rect.y() + (rect.height() - self.CELL_SIZE) // 2
            x = rect.x()
            
            for m in range(1, 13):
                for w in range(1, 5):
                    status = data.get(f"{m}_{w}", 0)
                    slot_rect = QRect(x, y_center, self.CELL_SIZE, self.CELL_SIZE)
                    
                    if status == 1:
                        painter.setBrush(QBrush(self.color_success))
                        painter.setPen(self.border_pen)
                        painter.drawRect(slot_rect)
                        painter.setPen(QPen(Qt.GlobalColor.black))
                        painter.drawText(slot_rect, Qt.AlignmentFlag.AlignCenter, "✓")
                    elif status == -1:
                        painter.setBrush(QBrush(self.color_fail))
                        painter.setPen(self.border_pen)
                        painter.drawRect(slot_rect)
                        painter.setPen(QPen(QColor("#ffcccc")))
                        painter.drawText(slot_rect, Qt.AlignmentFlag.AlignCenter, "✕")
                    else:
                        painter.setBrush(QBrush(self.color_pending))
                        painter.setPen(self.border_pen)
                        painter.drawRect(slot_rect)
                        # Small week number in pending cells
                        painter.setPen(QColor("#707070"))
                        f = painter.font(); f.setPointSize(7); painter.setFont(f)
                        painter.drawText(slot_rect, Qt.AlignmentFlag.AlignCenter, str(w))
                    
                    x += self.CELL_SIZE + self.SPACING
                
                x += self.MONTH_SPACING
                
            painter.restore()
            return
        
        super().paint(painter, option, index)


    def sizeHint(self, option, index):
        if index.column() == 2:
            month_width = 4 * (self.CELL_SIZE + self.SPACING)
            total_width = (month_width * 12) + (11 * self.MONTH_SPACING)
            return QSize(total_width, self.CELL_SIZE + 4)
        return super().sizeHint(option, index)

    def editorEvent(self, event, model, option, index):
        """Maneja clics en celdas de la grilla de pesca."""
        if event.type() == event.Type.MouseButtonRelease:
            if index.column() == 2 and index.data(FishingModel.TypeRole) == "account":
                click_x = event.pos().x()
                rect = option.rect
                
                cell_total = self.CELL_SIZE + self.SPACING
                month_width = 4 * cell_total
                month_block = month_width + self.MONTH_SPACING
                
                rel_x = click_x - rect.x()
                if rel_x < 0: return False
                
                m_idx = int(rel_x // month_block)
                month = m_idx + 1
                if not (1 <= month <= 12): return False
                
                local_x = rel_x - (m_idx * month_block)
                w_idx = int(local_x // cell_total)
                week = w_idx + 1
                if not (1 <= week <= 4): return False
                
                account = index.data(FishingModel.RawDataRole)
                if not account: return False
                
                activity = getattr(account, 'fishing_activity_map', {})
                key = f"{month}_{week}"
                current = activity.get(key, 0)
                
                # Validacion secuencial
                if week > 1:
                     prev_key = f"{month}_{week-1}"
                     if activity.get(prev_key, 0) == 0: return True
                
                new_status = 1 if current == 0 else (-1 if current == 1 else 0)
                
                if account.characters:
                    char_id = account.characters[0].id
                    if self.controller:
                        year = getattr(model, '_year', 2026)
                        self.controller.update_fishing_status(char_id, year, month, week, new_status)
                        model.update_fishing_status(index, month, week, new_status)
                        
                return True
                
        return super().editorEvent(event, model, option, index)
