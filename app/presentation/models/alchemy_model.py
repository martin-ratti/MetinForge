from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt, QVariant
from app.utils.logger import logger

class AlchemyModel(QAbstractItemModel):
    """Modelo jerarquico para AlchemyView: Root -> Store -> GameAccount."""
    
    RawDataRole = Qt.ItemDataRole.UserRole + 1
    TypeRole = Qt.ItemDataRole.UserRole + 2
    GridDataRole = Qt.ItemDataRole.UserRole + 3
    CordsRole = Qt.ItemDataRole.UserRole + 4
    
    def __init__(self, data=None, event_id=None, controller=None):
        super().__init__()
        self._data = data or []
        self._event_id = event_id
        self._controller = controller
        self._cords_summary = {}
        self._current_day = 1
        self._headers = ["Cuenta", "Slots", "Mezclador", "Registro Diario", "Cords"]

    def set_data(self, data, event_id, cords_summary=None):
        self.beginResetModel()
        self._data = data
        self._event_id = event_id
        self._cords_summary = cords_summary or {}
        self.endResetModel()

    def get_total_event_cords(self):
        """Calcula el total de cords desde el resumen cacheado."""
        total = 0
        for daily_records in self._cords_summary.values():
            total += sum(daily_records.values())
        return total

    def update_daily_status(self, index, day, status):
        """Actualiza el estado de un dia en la UI (optimistic update)."""
        if not index.isValid(): return
        
        item_type = index.data(self.TypeRole)
        if item_type != "account": return
        
        account = index.data(self.RawDataRole)
        
        if not hasattr(account, 'current_event_activity'):
             account.current_event_activity = {}
        
        account.current_event_activity[day] = status
        
        if account.id not in self._cords_summary:
             self._cords_summary[account.id] = {}
        
        self._cords_summary[account.id][day] = self._cords_summary[account.id].get(day, 0)

        cords_index = self.index(index.row(), 4, index.parent())
        
        self.dataChanged.emit(index, index, [self.GridDataRole])
        self.dataChanged.emit(cords_index, cords_index, [self.CordsRole, Qt.ItemDataRole.DisplayRole])

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            if 0 <= row < len(self._data):
                return self.createIndex(row, column, self._data[row])
        else:
            parent_item = parent.internalPointer()
            if isinstance(parent_item, dict) and 'accounts' in parent_item:
                accounts = parent_item['accounts']
                if 0 <= row < len(accounts):
                    return self.createIndex(row, column, accounts[row])
        
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()

        if isinstance(child_item, dict) and 'store' in child_item:
            return QModelIndex()

        for r, store_data in enumerate(self._data):
            if child_item in store_data.get('accounts', []):
                return self.createIndex(r, 0, store_data)
                
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self._data)
        
        parent_item = parent.internalPointer()
        if isinstance(parent_item, dict):
            return len(parent_item.get('accounts', []))
            
        return 0

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        is_store = isinstance(item, dict)
        column = index.column()

        if role == self.RawDataRole:
            return item
            
        if role == self.TypeRole:
            return "store" if is_store else "account"

        if is_store:
            if role == Qt.ItemDataRole.DisplayRole:
                if column == 0:
                    return item['store'].email
            return None

        account = item
        
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return account.username
            elif column == 1:
                if account.characters:
                    return str(account.characters[0].slots)
                return "5"
            elif column == 2:
                return account.characters[0].name if account.characters else "-"
            elif column == 4:
                if self._current_day:
                    if account.id in self._cords_summary:
                        return str(self._cords_summary[account.id].get(self._current_day, 0))
                    return "0"
                return "0" 

        if role == self.GridDataRole and column == 3:
            return getattr(account, 'current_event_activity', {})

        if role == self.CordsRole and column == 4:
            if account.id in self._cords_summary:
                return self._cords_summary[account.id].get(self._current_day, 0)
            return 0

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [1, 4]:
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
            
        flags = super().flags(index)
        
        if index.column() == 4 and index.data(self.TypeRole) == "account":
            return flags | Qt.ItemFlag.ItemIsEditable
            
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
            
        if index.column() == 4 and role == Qt.ItemDataRole.EditRole:
             item_type = index.data(self.TypeRole)
             if item_type == "account":
                 account = index.data(self.RawDataRole)
                 
                 if account.id not in self._cords_summary:
                     self._cords_summary[account.id] = {}
                 
                 self._cords_summary[account.id][self._current_day] = value
                 
                 if self._controller and self._event_id:
                     try:
                         self._controller.update_daily_cords(account.id, self._event_id, self._current_day, value)
                     except AttributeError:
                         pass

                 self.dataChanged.emit(index, index, [self.CordsRole, Qt.ItemDataRole.DisplayRole])
                 
                 return True
                 
        return False

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None
