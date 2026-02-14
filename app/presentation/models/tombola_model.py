from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from app.utils.logger import logger

from app.application.dtos import StoreAccountDTO, GameAccountDTO, TombolaCharacterDTO

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
        
        # En TombolaDTO, el mapa esta en el primer personaje
        if account.characters:
            char = account.characters[0]
            if isinstance(char, TombolaCharacterDTO):
                char.daily_status_map[day] = status
        
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

        account = item
        
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return account.username
            elif column == 1:
                # Nombre del personaje (Mezclador)
                return account.characters[0].name if account.characters else "-"
        
        if role == self.GridDataRole and column == 2:
            if account.characters:
                char = account.characters[0]
                if hasattr(char, 'daily_status_map'):
                    return char.daily_status_map
            return {}

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [1]: 
                return Qt.AlignmentFlag.AlignLeft
        
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None
