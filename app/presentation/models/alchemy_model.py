from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt, QVariant
from app.utils.logger import logger

class AlchemyModel(QAbstractItemModel):
    """
    Modelo jerárquico para AlchemyView optimizado para velocidad y virtualización.
    Estructura:
    - Root
      - Store (Group)
        - GameAccount (Row)
    """
    
    # Custom Roles
    RawDataRole = Qt.ItemDataRole.UserRole + 1  # Retorna el objeto subyacente (Store o GameAccount)
    TypeRole = Qt.ItemDataRole.UserRole + 2     # "store" o "account"
    GridDataRole = Qt.ItemDataRole.UserRole + 3 # Dict con estado de días {day: status}
    CordsRole = Qt.ItemDataRole.UserRole + 4    # Int, cantidad de cords
    
    def __init__(self, data=None, event_id=None, controller=None):
        super().__init__()
        self._data = data or [] # List of dicts: {'store': Store, 'accounts': [GameAccount]}
        self._event_id = event_id
        self._controller = controller
        self._cords_summary = {} # {account_id: {day: count}}
        self._current_day = 1 # Default
        
        # Headers: Account, Slots, Mezclador, Grid (Days), Cords
        self._headers = ["Cuenta", "Slots", "Mezclador", "Registro Diario", "Cords"]

    def set_data(self, data, event_id, cords_summary=None):
        self.beginResetModel()
        self._data = data
        self._event_id = event_id
        self._cords_summary = cords_summary or {}
        self.endResetModel()

    def get_total_event_cords(self):
        """Calculates total cords from cached summary"""
        total = 0
        for daily_records in self._cords_summary.values():
            total += sum(daily_records.values())
        return total

    def update_daily_status(self, index, day, status):
        """Called by delegate or view to update data"""
        if not index.isValid(): return
        
        item_type = index.data(self.TypeRole)
        if item_type != "account": return
        
        account = index.data(self.RawDataRole)
        # Update logic handled by controller, here we just refresh view
        # Ideally controller returns success, then we emit dataChanged
        # For responsiveness, we can emit immediately if we trust the operation
        
        # Calculate range to update (columns involved)
        # Grid is column 3
        # Update Local State (Optimistic UI)
        # account is a reference to the dict/object in self._data
        if not hasattr(account, 'current_event_activity'):
             account.current_event_activity = {}
        
        # Calculate Cord diff for local update
        old_status = account.current_event_activity.get(day, 0)
        
        # Update Status
        account.current_event_activity[day] = status
        
        # Update Cords Summary Local
        # Status 1 (Success) adds 1 cord? Or depends on logic?
        # Assuming status 1 = +1 count for that day if "Success" implies getting a Cor.
        # But wait, grid status is usually just "Done/Fail". 
        # Check what "1" means. Usually means "Success".
        # Let's verify cords count logic. Usually controller calculates it.
        # Simple heuristic: If changed to 1, add 1. If changed from 1 to 0/-1, remove 1.
        
        if account.id not in self._cords_summary:
             self._cords_summary[account.id] = {}
        
        # Don't change cords count automatically. 
        # Cords count is strictly manual input.
        
        self._cords_summary[account.id][day] = self._cords_summary[account.id].get(day, 0)

        # Emit change for Grid AND Cords column (4)
        # We need index for column 4.
        cords_index = self.index(index.row(), 4, index.parent())
        
        self.dataChanged.emit(index, index, [self.GridDataRole])
        self.dataChanged.emit(cords_index, cords_index, [self.CordsRole, Qt.ItemDataRole.DisplayRole])

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
            # Verify parent is a dict (Store Data Structure)
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
        # This is expensive O(N) search. 
        # Optimization: We can wrap items in TreeItem objects to hold parent ref.
        # given the scale (hundreds of stores?), linear search might be acceptable but risky for "Extreme Speed".
        # Let's try linear search first, usually "parent()" is called less often than "data()"
        # Or better: construct a map during set_data? 
        # For now, let's look up.
        
        for r, store_data in enumerate(self._data):
            if child_item in store_data.get('accounts', []):
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
            
        # Accounts have no children
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

        # --- STORE ROW (HEADER-LIKE) ---
        if is_store:
            if role == Qt.ItemDataRole.DisplayRole:
                if column == 0:
                    return f"📧 {item['store'].email}"
            return None

        # --- ACCOUNT ROW ---
        # item is GameAccount object
        account = item
        
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0: # Account Name
                return account.username
            elif column == 1: # Slots
                # Return 'slots' from the first character (since format is 1 char per account usually)
                if account.characters:
                    return str(account.characters[0].slots)
                return "5"
            elif column == 2: # Character Name (Main/Alchemist)
                # Assumes Import Controller sorts chars so 0 is Alchemist
                return account.characters[0].name if account.characters else "-"
            elif column == 4: # Cords (Current Day usually, or Total?)
                # Controller usually provides summary for current context
                # We need access to specific day cords.
                # Let's assume we want current day cords here.
                # Logic to determine day should be passed or fetched.
                # For now returning None, Delegated will handle editor/display via custom role
                # UPDATE: User wants Total Cords for the account (sum of checks? or specific field?)
                # User said: "Falta el contador de cors por cada cuenta". 
                # This usually means the daily cords input we had before.
                # In the old view, we had a SpinBox for "Cords Hoy".
                # If we want to show it in column 4, we need to know "Current Day".
                # The model doesn't know "Current Day" unless we pass it or store it.
                # Let's assume column 4 is "Cords Hoy" based on a settable "current_day" property in model.
                if self._current_day:
                    if account.id in self._cords_summary:
                        return str(self._cords_summary[account.id].get(self._current_day, 0))
                    return "0"
                return "0" 

        if role == self.GridDataRole and column == 3:
            return getattr(account, 'current_event_activity', {})

        if role == self.CordsRole and column == 4:
            # Return cords for the specific account and current day
            # cords_summary structure needs to be checked. 
            # In AlchemyView it was: cords_summary = {acc_id: {day: count}}
            if account.id in self._cords_summary:
                # Use cords summary if available, but also check local state updates?
                # Ideally _cords_summary should be updated too.
                return self._cords_summary[account.id].get(self._current_day, 0)
            return 0

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [1, 4]: # Slots, Cords
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
            
        flags = super().flags(index)
        
        # Enable editing for Cords column (4) if it's an account
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
                 
                 # Update Local Summary
                 if account.id not in self._cords_summary:
                     self._cords_summary[account.id] = {}
                 
                 self._cords_summary[account.id][self._current_day] = value
                 
                 # Notify Controller First (Persistence)
                 if self._controller and self._event_id:
                     try:
                         self._controller.update_daily_cords(account.id, self._event_id, self._current_day, value)
                     except AttributeError:
                         pass

                 # Emit change (View Refresh)
                 self.dataChanged.emit(index, index, [self.CordsRole, Qt.ItemDataRole.DisplayRole])
                 
                 return True
                 
        return False

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None
