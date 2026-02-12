from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from app.presentation.models.fishing_model import FishingModel

class FishingGridDelegate(QStyledItemDelegate):
    """
    Delegate for rendering Annual Fishing Grid (12 Months x 4 Weeks) in a single cell.
    """
    
    # Constants
    MONTH_WIDTH = 28 # Compressed width for month block
    WEEK_HEIGHT = 14 # Height per week? No, usually 4 weeks horizontally or vertically?
    # Original view had: 12 Months (Columns?) x 4 Weeks (Rows inside?) or Buttons?
    # Original: Horizontal Month Frames, inside 4 buttons.
    # Let's do: 12 Columns (Months) * 4 Sub-columns (Weeks)? Too wide.
    # Data Dense: 12 blocks horizontally. Inside each block, 4 small squares (2x2 or 4x1).
    # Let's try 4x1 vertical stack or 2x2.
    # Account row height is approx 24px (Data Dense Standard).
    # 24px height allows for 2 rows of 10px? Or just 4 tiny dots 4x4?
    # Better: 12 Months horizontally. Each month has 4 weeks vertically? No space.
    # Standard: 12 Months columns. Inside each column, 4 items.
    
    # Let's stick to strict Data Dense:
    # 1 Row per Account.
    # Grid Cell contains 12 "Month Blocks".
    # Each "Month Block" contains 4 "Week Boxes" (2x2 grid).
    # Box size: 8x8px. Spacing 1px.
    # Month Block Size: (8+1+8) x (8+1+8) = 17x17px. + Margin.
    # Total Height 24px fits perfectly.
    
    # Revised Layout: 12 Months, but Weeks visually separated
    # User requested "Separated by Week". 
    # Let's use 16px boxes, but spacing between weeks is larger (e.g. 4px)
    # Spacing between months is even larger (e.g. 12px)
    
    BOX_SIZE = 16
    BG_BOX_SIZE = 22 # Background block for the week
    BOX_SPACING = 6 # Distinct separation between weeks
    MONTH_SPACING = 16 # Larger separation between months
    
    def __init__(self, parent=None, controller=None, model=None):
        super().__init__(parent)
        self.controller = controller
        self.model = model
        
        # Colors
        self.color_pending = QColor("#2b2b2b")
        self.color_success = QColor("#4fc3f7") # Light Blue for Fish
        self.color_fail = QColor("#ef5350")    # Red for Fail
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
        
        # Iterate 12 Months
        for m in range(1, 13):
            # Draw Month Label centered above/below?
            # Or just draw weeks 1-4
            
            # Label
            # painter.drawText(QRect(x_offset, rect.y(), ..., 15), ..., str(m))
            
            # 4 Weeks per month
            for w in range(1, 5):
                status = data.get(f"{m}_{w}", 0)
                
                # Draw Week Box (Container)
                # Let's make it look like a slot
                slot_rect = QRect(x_offset, y_center - self.BOX_SIZE // 2, self.BOX_SIZE, self.BOX_SIZE)
                
                # Color
                color = QColor("#2b2b2b") # Empty slot
                if status == 1: color = QColor("#00bcd4") # Cyan
                elif status == -1: color = QColor("#f44336") # Red
                
                # Fill
                painter.fillRect(slot_rect, color)
                
                # Border
                painter.setPen(QColor("#555555"))
                # If active, maybe highlight border?
                painter.drawRect(slot_rect)
                
                # Draw Month Number above first week only?
                if w == 1:
                     painter.setPen(QColor("#808080"))
                     font = painter.font(); font.setPointSize(8); painter.setFont(font)
                     painter.drawText(QRect(x_offset, rect.y() + 2, self.BOX_SIZE, 12), Qt.AlignmentFlag.AlignCenter, str(m))

                x_offset += self.BOX_SIZE + self.BOX_SPACING
            
            # Extra space between months
            x_offset += (self.MONTH_SPACING - self.BOX_SPACING)
            
        painter.restore()

    def sizeHint(self, option, index):
        # 12 months * (4 weeks * (size+space)) + 11 * extra_month_space
        month_width = (4 * (self.BOX_SIZE + self.BOX_SPACING))
        total_width = (month_width * 12) + (11 * (self.MONTH_SPACING - self.BOX_SPACING)) + 40
        return QSize(total_width, 46)

    def editorEvent(self, event, model, option, index):
        if event.type() == event.Type.MouseButtonRelease:
            if index.column() == 2 and index.data(FishingModel.TypeRole) == "account":
                click_x = event.pos().x()
                click_y = event.pos().y()
                rect = option.rect
                
                # Reverse Math
                start_x = rect.x() + 4
                block_height = (self.BOX_SIZE * 2) + self.BOX_SPACING
                start_y = rect.y() + (rect.height() - block_height) // 2
                
                # Determine Month
                month_block_width = (self.BOX_SIZE*2 + self.BOX_SPACING) + self.MONTH_SPACING
                rel_x = click_x - start_x
                
                if rel_x < 0: return False
                
                m_idx = rel_x // month_block_width
                month = m_idx + 1
                
                if not (1 <= month <= 12): return False
                
                # Determine Week inside Month Block
                # Rel coords inside block
                block_x_start = start_x + (m_idx * month_block_width)
                local_x = click_x - block_x_start
                local_y = click_y - start_y
                
                col = local_x // (self.BOX_SIZE + self.BOX_SPACING)
                row = local_y // (self.BOX_SIZE + self.BOX_SPACING)
                
                # Map row/col to Week Num (1,2,3,4)
                # (0,0)->1, (1,0)->2, (0,1)->3, (1,1)->4
                week = 0
                if row == 0 and col == 0: week = 1
                elif row == 0 and col == 1: week = 2
                elif row == 1 and col == 0: week = 3
                elif row == 1 and col == 1: week = 4
                
                if week == 0: return False
                
                # Logic
                account = index.data(FishingModel.RawDataRole)
                if not account: return False
                
                activity = getattr(account, 'fishing_activity_map', {})
                key = f"{month}_{week}"
                current = activity.get(key, 0)
                
                # Sequential Check (Optional: Require previous week done?)
                # User request: "Data sense aplicable a pesca".
                # Usually implies strict order.
                # Let's verify previous week.
                # prev_key needed... logic: (m, w-1) or (m-1, 4) if w=1
                # Complicated. Let's skip strict validation for click ease for now?
                # Or simplistic: w>1 check w-1.
                if week > 1:
                     prev_key = f"{month}_{week-1}"
                     if activity.get(prev_key, 0) == 0: return True # Block
                
                # Toggle
                new_status = 1 if current == 0 else (-1 if current == 1 else 0)
                
                # Update
                if account.characters:
                    char_id = account.characters[0].id
                    if self.controller:
                        year = getattr(model, '_year', 2026)
                        self.controller.update_fishing_status(char_id, year, month, week, new_status)
                        model.update_fishing_status(index, month, week, new_status)
                        
                return True
                
        return super().editorEvent(event, model, option, index)
