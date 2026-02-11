from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from app.presentation.models.alchemy_model import AlchemyModel

class DailyGridDelegate(QStyledItemDelegate):
    """
    Delegado gráfico puro para renderizar la grilla de 30/31 días.
    Evita crear widgets por cada celda.
    """
    
    # Constants
    CELL_SIZE = 22
    SPACING = 2
    
    def __init__(self, parent=None, total_days=30, controller=None, model=None):
        super().__init__(parent)
        self.total_days = total_days
        self.controller = controller
        # Colores cacheados
        self.color_pending = QColor("#2b2b2b")
        self.color_success = QColor("#d4af37") # Gold
        self.color_fail = QColor("#550000")    # Dark Red
        self.border_pen = QPen(QColor("#5d4d2b"))
        self.text_pen = QPen(QColor("#ffffff"))

    def paint(self, painter, option, index):
        item_type = index.data(AlchemyModel.TypeRole)
        
        # Caso Especial: Header de Días en la fila de Store
        if item_type == "store" and index.column() == 3:
            painter.save()
            rect = option.rect
            
            # Fondo oscuro para el header de dias
            painter.fillRect(rect, QColor("#102027")) # Mismo que store header
            
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

        # Solo pintamos Grid en columna 3 para accounts
        if index.column() != 3:
            super().paint(painter, option, index)
            return
            
        painter.save()
        
        # Recuperar datos
        grid_data = index.data(AlchemyModel.GridDataRole) or {}
        
        rect = option.rect
        
        # Calcular posición inicial (centrado verticalmente si hay espacio)
        # Asumimos que la fila tiene altura suficiente
        start_x = rect.x()
        start_y = rect.y() + (rect.height() - self.CELL_SIZE) // 2
        
        current_x = start_x
        
        # Iterar días
        for day in range(1, self.total_days + 1):
            status = grid_data.get(day, 0) # 0, 1, -1
            
            # Definir rect del día
            day_rect = QRect(current_x, start_y, self.CELL_SIZE, self.CELL_SIZE)
            
            # Setup Brush/Color
            bg_brush = QBrush(self.color_pending)
            text_str = ""
            
            if status == 1:
                bg_brush = QBrush(self.color_success)
                text_str = "✓"
                painter.setPen(QPen(Qt.GlobalColor.black)) # Texto negro en oro
            elif status == -1:
                bg_brush = QBrush(self.color_fail)
                text_str = "✕"
                painter.setPen(QPen(QColor("#ffcccc")))
            else:
                painter.setPen(self.border_pen) # Borde dorado en gris
            
            # Dibujar Fondo y Borde
            painter.setBrush(bg_brush)
            # Solo borde si es pending, para otros rellenamos (o borde tambien)
            painter.drawRect(day_rect)
            
            # Dibujar Borde (siempre)
            painter.setPen(self.border_pen)
            painter.drawRect(day_rect)
            
            # Dibujar Texto (Centrado) - Check o Cruz
            if text_str:
                painter.drawText(day_rect, Qt.AlignmentFlag.AlignCenter, text_str)
            
            # Dibujar Número de Día (Siempre, pequeño en esquina o centro si no hay status)
            # User wants "números de los días arriba".
            # Option A: Header row above the grid. (Hard in TreeView single cell)
            # Option B: Draw small number inside cell.
            # Let's draw small number in top-left or centered if empty.
            
            # Draw day number centered if status is 0 (Pending) to guide user
            # If status is set, maybe hide it or show simplified?
            # User request: "falta nros de los dias arriba como columna". 
            # If we can't easily add a header row per store, lets draw it inside.
            
            painter.setPen(QColor("#707070"))
            font = painter.font()
            font.setPointSize(7)
            painter.setFont(font)
            
            # Si tiene estado, dibujamos el numero chiquito arriba a la izquierda
            # Si no tiene estado, lo dibujamos en el centro (mas grande?) No, mantener consistencia.
            # Mejor: Arriba del cuadrado? No podemos salir del rect.
            # Dentro del cuadrado, arriba izquierda o derecha.
            
            year_rect = QRect(day_rect.x() + 2, day_rect.y() + 2, 15, 10)
            painter.drawText(year_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(day))
            
            current_x += self.CELL_SIZE + self.SPACING
            
        painter.restore()

    def sizeHint(self, option, index):
        if index.column() == 3:
            width = (self.CELL_SIZE + self.SPACING) * self.total_days
            return QSize(width, self.CELL_SIZE + 4) # +4 padding vert
        return super().sizeHint(option, index)

    def editorEvent(self, event, model, option, index):
        """Manejar clics directamente para actualizar estado sin modo edición"""
        if event.type() == event.Type.MouseButtonRelease:
            if index.column() == 3 and index.data(AlchemyModel.TypeRole) == "account":
                # Calcular qué día se clickeó
                click_x = event.pos().x()
                rect = option.rect
                
                # IMPORTANT: Use exact same math as paint()
                # paint: current_x starts at rect.x()
                # cell width = CELL_SIZE, spacing = SPACING
                rel_x = click_x - rect.x()
                
                # cell_total_width = CELL_SIZE + SPACING
                # idx = rel_x // cell_total_width
                cell_total_width = self.CELL_SIZE + self.SPACING
                idx = rel_x // cell_total_width
                day = idx + 1
                
                if 1 <= day <= self.total_days:
                    # Get Account Data
                    account = index.data(AlchemyModel.RawDataRole)
                    if not account: return False

                    activity = getattr(account, 'current_event_activity', {})
                    current_status = activity.get(day, 0)
                    
                    # --- VALIDATION START ---
                    # Rule: Cannot modify Day N if Day N-1 is not Done/Success (status != 0)
                    # Exception: Day 1
                    if day > 1:
                        prev_day = day - 1
                        prev_status = activity.get(prev_day, 0)
                        if prev_status == 0:
                            # Block interaction
                            # Optional: Emit signal or show tooltip?
                            # For speed, just ignore.
                            return True
                    # --- VALIDATION END ---

                    # Toggle logic: 0 -> 1 -> -1 -> 0
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
                                
                    return True # Evento consumido
                    
        return super().editorEvent(event, model, option, index)
