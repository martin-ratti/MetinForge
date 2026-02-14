from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from app.utils.logger import logger
from app.application.dtos import StoreAccountDTO, GameAccountDTO

class FishingModel(QAbstractItemModel):
    """Modelo jerarquico para FishingView: Root -> Store -> GameAccount."""
    
    RawDataRole = Qt.ItemDataRole.UserRole + 1
    TypeRole = Qt.ItemDataRole.UserRole + 2
    GridDataRole = Qt.ItemDataRole.UserRole + 3
    
    def __init__(self, data=None, year=None, controller=None):
        super().__init__()
        self._data = data or [] 
        self._year = year
        self._controller = controller
        self._headers = ["Cuenta", "Pescador", "Registro Anual"]

    def set_data(self, data, year):
        self.beginResetModel()
        self._data = data
        self._year = year
        self.endResetModel()

    def update_fishing_status(self, index, month, week, status):
        """Actualiza estado de pesca en la UI (optimistic update)."""
        if not index.isValid(): return
        
        item_type = index.data(self.TypeRole)
        if item_type != "account": return
        
        account_dto = index.data(self.RawDataRole)
        if not account_dto.characters: return
        
        char_dto = account_dto.characters[0]
        
        key = f"{month}_{week}"
        char_dto.fishing_activity_map[key] = status
        
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
            if isinstance(parent_item, StoreAccountDTO):
                accounts = parent_item.game_accounts
                if 0 <= row < len(accounts):
                    return self.createIndex(row, column, accounts[row])
        
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()

        if isinstance(child_item, StoreAccountDTO):
            return QModelIndex()

        for r, store_dto in enumerate(self._data):
            if child_item in store_dto.game_accounts:
                return self.createIndex(r, 0, store_dto)
                
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self._data)
        
        parent_item = parent.internalPointer()
        if isinstance(parent_item, StoreAccountDTO):
            return len(parent_item.game_accounts)
            
        return 0

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        is_store = isinstance(item, StoreAccountDTO)
        column = index.column()

        if role == self.RawDataRole:
            return item
            
        if role == self.TypeRole:
            return "store" if is_store else "account"

        if is_store:
            if role == Qt.ItemDataRole.DisplayRole:
                if column == 0:
                    return item.email
            return None

        account = item # GameAccountDTO
        
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return account.username
            elif column == 1:
                chars = account.characters
                first_char = chars[0] if chars else None
                name = first_char.name if first_char else "-"
                return name.split('_')[0] if '_' in name else name
        
        if role == self.GridDataRole and column == 2:
            chars = account.characters
            first_char = chars[0] if chars else None
            return first_char.fishing_activity_map if first_char else {}

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [1]: 
                return Qt.AlignmentFlag.AlignLeft
        
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None
