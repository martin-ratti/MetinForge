from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from app.utils.logger import logger

class TombolaModel(QAbstractItemModel):
    """
    Hierarchical Model for TombolaView (Virtualization).
    Structure:
    - Root
      - Store (Group)
        - GameAccount (Row)
    """
    
    # Custom Roles
    RawDataRole = Qt.ItemDataRole.UserRole + 1  # Returns underlying object (Store or GameAccount)
    TypeRole = Qt.ItemDataRole.UserRole + 2     # "store" or "account"
    GridDataRole = Qt.ItemDataRole.UserRole + 3 # Dict with daily status {day: status}
    
    def __init__(self, data=None, event_id=None, controller=None):
        super().__init__()
        self._data = data or [] # List of dicts: {'store': Store, 'accounts': [GameAccount]}
        self._event_id = event_id
        self._controller = controller
        
        # Headers: Account, Character, Grid (Days)
        # Tombola usually doesn't track Cords or Slots explicitly in the view, just the grid.
        self._headers = ["Cuenta", "Personaje", "Registro Diario"]

    def set_data(self, data, event_id):
        self.beginResetModel()
        self._data = data
        self._event_id = event_id
        self.endResetModel()

    def update_daily_status(self, index, day, status):
        """Called by delegate or view to update data reflected in UI"""
        if not index.isValid(): return
        
        item_type = index.data(self.TypeRole)
        if item_type != "account": return
        
        account = index.data(self.RawDataRole)
        
        # Update Local State (Optimistic UI)
        if not hasattr(account, 'current_event_activity'):
             account.current_event_activity = {}
        
        # Update Status
        account.current_event_activity[day] = status
        
        # Emit change for Grid Column (2)
        grid_index = self.index(index.row(), 2, index.parent())
        self.dataChanged.emit(grid_index, grid_index, [self.GridDataRole])

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            # Top level: Stores
            if 0 <= row < len(self._data):
                return self.createIndex(row, column, self._data[row])
        else:
            # Second level: Accounts within a Store
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

        # If child is a Store Dict, it has no parent (Root)
        if isinstance(child_item, dict) and 'store' in child_item:
            return QModelIndex()

        # If child is GameAccount, parent is the Store Dict containing it
        for r, store_data in enumerate(self._data):
            if child_item in store_data.get('accounts', []):
                # We return the parent index with column 0
                return self.createIndex(r, 0, store_data)
                
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            # Root rows = Number of Stores
            return len(self._data)
        
        parent_item = parent.internalPointer()
        if isinstance(parent_item, dict):
            # Store rows = Number of Accounts
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

        # --- STORE ROW ---
        if is_store:
            if role == Qt.ItemDataRole.DisplayRole:
                if column == 0:
                    return f"📧 {item['store'].email}"
            return None

        # --- ACCOUNT ROW ---
        account = item
        
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0: # Account Name
                return account.username
            elif column == 1: # Character Name
                 # Sort chars by ID to ensure consistency
                chars = sorted(account.characters, key=lambda x: x.id) if account.characters else []
                first_char = chars[0] if chars else None
                name = first_char.name if first_char else "-"
                # Clean name (remove prefix if present, e.g. "s1_Name")
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
