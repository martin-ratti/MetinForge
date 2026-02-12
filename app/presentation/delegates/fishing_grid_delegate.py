from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from app.presentation.models.fishing_model import FishingModel

class FishingGridDelegate(QStyledItemDelegate):
    """Delegate para renderizar la grilla anual de pesca (12 Meses x 4 Semanas) en una celda."""
    
    BOX_SIZE = 16
    BG_BOX_SIZE = 22
    BOX_SPACING = 6
    MONTH_SPACING = 16
    
    def __init__(self, parent=None, controller=None, model=None):
        super().__init__(parent)
        self.controller = controller
        self.model = model
        
        self.color_pending = QColor("#2b2b2b")
        self.color_success = QColor("#4fc3f7")
        self.color_fail = QColor("#ef5350")
        self.border_pen = QPen(QColor("#5d4d2b"))

    def paint(self, painter, option, index):
        if not index.isValid():
            return

        data = index.data(FishingModel.GridDataRole)
        if not data: data = {}
        
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = option.rect
        y_center = rect.y() + rect.height() // 2
        x_offset = rect.x() + 10
        
        for m in range(1, 13):
            for w in range(1, 5):
                status = data.get(f"{m}_{w}", 0)
                
                slot_rect = QRect(x_offset, y_center - self.BOX_SIZE // 2, self.BOX_SIZE, self.BOX_SIZE)
                
                color = QColor("#2b2b2b")
                if status == 1: color = QColor("#00bcd4")
                elif status == -1: color = QColor("#f44336")
                
                painter.fillRect(slot_rect, color)
                
                painter.setPen(QColor("#555555"))
                painter.drawRect(slot_rect)
                
                if w == 1:
                     painter.setPen(QColor("#808080"))
                     font = painter.font(); font.setPointSize(8); painter.setFont(font)
                     painter.drawText(QRect(x_offset, rect.y() + 2, self.BOX_SIZE, 12), Qt.AlignmentFlag.AlignCenter, str(m))

                x_offset += self.BOX_SIZE + self.BOX_SPACING
            
            x_offset += (self.MONTH_SPACING - self.BOX_SPACING)
            
        painter.restore()

    def sizeHint(self, option, index):
        month_width = (4 * (self.BOX_SIZE + self.BOX_SPACING))
        total_width = (month_width * 12) + (11 * (self.MONTH_SPACING - self.BOX_SPACING)) + 40
        return QSize(total_width, 46)

    def editorEvent(self, event, model, option, index):
        """Maneja clics en celdas de la grilla de pesca."""
        if event.type() == event.Type.MouseButtonRelease:
            if index.column() == 2 and index.data(FishingModel.TypeRole) == "account":
                click_x = event.pos().x()
                click_y = event.pos().y()
                rect = option.rect
                
                start_x = rect.x() + 4
                block_height = (self.BOX_SIZE * 2) + self.BOX_SPACING
                start_y = rect.y() + (rect.height() - block_height) // 2
                
                month_block_width = (self.BOX_SIZE*2 + self.BOX_SPACING) + self.MONTH_SPACING
                rel_x = click_x - start_x
                
                if rel_x < 0: return False
                
                m_idx = rel_x // month_block_width
                month = m_idx + 1
                
                if not (1 <= month <= 12): return False
                
                block_x_start = start_x + (m_idx * month_block_width)
                local_x = click_x - block_x_start
                local_y = click_y - start_y
                
                col = local_x // (self.BOX_SIZE + self.BOX_SPACING)
                row = local_y // (self.BOX_SIZE + self.BOX_SPACING)
                
                week = 0
                if row == 0 and col == 0: week = 1
                elif row == 0 and col == 1: week = 2
                elif row == 1 and col == 0: week = 3
                elif row == 1 and col == 1: week = 4
                
                if week == 0: return False
                
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
