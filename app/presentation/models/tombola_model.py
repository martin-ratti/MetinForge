from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from app.utils.logger import logger

class TombolaModel(QAbstractItemModel):
    """Modelo jerarquico para TombolaView: Root -> Store -> GameAccount."""
    
    RawDataRole = Qt.ItemDataRole.UserRole + 1
    TypeRole = Qt.ItemDataRole.UserRole + 2
    GridDataRole = Qt.ItemDataRole.UserRole + 3
    
    def __init__(self, data=None, event_id=None, controller=None):
        super().__init__()
        self._data = data or []
        self._event_id = event_id
        self._controller = controller
        self._headers = ["Cuenta", "Personaje", "Registro Diario"]

    def set_data(self, data, event_id):
        self.beginResetModel()
        self._data = data
        self._event_id = event_id
        self.endResetModel()

    def update_daily_status(self, index, day, status):
        """Actualiza estado diario en la UI (optimistic update)."""
        if not index.isValid(): return
        
        item_type = index.data(self.TypeRole)
        if item_type != "account": return
        
        account = index.data(self.RawDataRole)
        
        if not hasattr(account, 'current_event_activity'):
             account.current_event_activity = {}
        
        account.current_event_activity[day] = status
        
        grid_index = self.index(index.row(), 2, index.parent())
        self.dataChanged.emit(grid_index, grid_index, [self.GridDataRole])

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
                chars = sorted(account.characters, key=lambda x: x.id) if account.characters else []
                first_char = chars[0] if chars else None
                name = first_char.name if first_char else "-"
                return name.split('_')[0] if '_' in name else name
        
        if role == self.GridDataRole and column == 2:
            return getattr(account, 'current_event_activity', {})

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [1]: 
                return Qt.AlignmentFlag.AlignLeft
        
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None
