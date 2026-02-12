from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QBrush, QPen
from app.presentation.models.tombola_model import TombolaModel

class TombolaGridDelegate(QStyledItemDelegate):
    """
    Delegate for rendering the 31-day Tombola Grid in a single cell.
    Optimized for Data Dense display.
    """
    
    # Constants for Density
    CELL_SIZE = 22
    SPACING = 2
    TOTAL_DAYS = 31
    
    def __init__(self, parent=None, controller=None, model=None):
        super().__init__(parent)
        self.controller = controller
        
        # Cached Colors
        self.color_pending = QColor("#2b2b2b")
        self.color_success = QColor("#d4af37") # Gold
        self.color_fail = QColor("#550000")    # Dark Red
        self.border_pen = QPen(QColor("#5d4d2b"))
        self.text_pen = QPen(QColor("#ffffff"))

    def paint(self, painter, option, index):
        item_type = index.data(TombolaModel.TypeRole)
        
        # --- STORE HEADER (Days Numbers) ---
        if item_type == "store" and index.column() == 2:
            painter.save()
            rect = option.rect
            
            # Dark background for header
            painter.fillRect(rect, QColor("#102027"))
            
            start_x = rect.x()
            start_y = rect.y() + (rect.height() - self.CELL_SIZE) // 2
            current_x = start_x
            
            painter.setPen(QColor("#a0a0a0"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(8)
            painter.setFont(font)

            # Draw day numbers
            for day in range(1, self.TOTAL_DAYS + 1):
                day_rect = QRect(current_x, start_y, self.CELL_SIZE, self.CELL_SIZE)
                painter.drawText(day_rect, Qt.AlignmentFlag.AlignCenter, str(day))
                current_x += self.CELL_SIZE + self.SPACING
            
            painter.restore()
            return

        # --- ACCOUNT ROW (Grid) ---
        if item_type == "account" and index.column() == 2:
            painter.save()
            
            grid_data = index.data(TombolaModel.GridDataRole) or {}
            rect = option.rect
            
            start_x = rect.x()
            start_y = rect.y() + (rect.height() - self.CELL_SIZE) // 2
            current_x = start_x
            
            for day in range(1, self.TOTAL_DAYS + 1):
                status = grid_data.get(day, 0) # 0, 1, -1
                
                day_rect = QRect(current_x, start_y, self.CELL_SIZE, self.CELL_SIZE)
                
                # Brush & Text
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
                
                # Draw
                painter.setBrush(bg_brush)
                painter.drawRect(day_rect)
                
                painter.setPen(self.border_pen)
                painter.drawRect(day_rect)
                
                if text_str:
                    painter.drawText(day_rect, Qt.AlignmentFlag.AlignCenter, text_str)
                else:
                    # Draw small day number if pending
                    painter.setPen(QColor("#707070"))
                    f = painter.font(); f.setPointSize(7); painter.setFont(f)
                    painter.drawText(QRect(day_rect.x()+2, day_rect.y()+2, 15, 10), 
                                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(day))

                current_x += self.CELL_SIZE + self.SPACING
            
            painter.restore()
            return
            
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        if index.column() == 2:
            width = (self.CELL_SIZE + self.SPACING) * self.TOTAL_DAYS
            return QSize(width, self.CELL_SIZE + 4)
        return super().sizeHint(option, index)

    def editorEvent(self, event, model, option, index):
        """Handle clicks on grid cells"""
        if event.type() == event.Type.MouseButtonRelease:
            if index.column() == 2 and index.data(TombolaModel.TypeRole) == "account":
                click_x = event.pos().x()
                rect = option.rect
                
                # Math must match paint()
                rel_x = click_x - rect.x()
                cell_total_width = self.CELL_SIZE + self.SPACING
                idx = rel_x // cell_total_width
                day = idx + 1
                
                if 1 <= day <= self.TOTAL_DAYS:
                    account = index.data(TombolaModel.RawDataRole)
                    if not account: return False

                    activity = getattr(account, 'current_event_activity', {})
                    current_status = activity.get(day, 0)
                    
                    # Sequential Validation (Optional, consistent with others)
                    if day > 1:
                        prev = activity.get(day - 1, 0)
                        if prev == 0: return True # Block gap filling if previous not done
                    
                    # Toggle Status
                    new_status = 0
                    if current_status == 0: new_status = 1
                    elif current_status == 1: new_status = -1
                    else: new_status = 0
                    
                    # Update DB & Model
                    if account.characters:
                        char_id = account.characters[0].id
                        if self.controller:
                            # Verify model has event_id
                            event_id = getattr(model, '_event_id', None)
                            if event_id:
                                self.controller.update_daily_status(char_id, day, new_status, event_id)
                                model.update_daily_status(index, day, new_status)
                                
                    return True
        return super().editorEvent(event, model, option, index)
