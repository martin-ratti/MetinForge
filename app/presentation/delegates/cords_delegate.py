from PyQt6.QtWidgets import QStyledItemDelegate, QSpinBox
from PyQt6.QtCore import Qt
from app.presentation.models.alchemy_model import AlchemyModel

class CordsDelegate(QStyledItemDelegate):
    """Delegate para editar la columna de Cords con un SpinBox."""
    
    def createEditor(self, parent, option, index):
        if index.column() != 4:
            return super().createEditor(parent, option, index)
            
        spinbox = QSpinBox(parent)
        spinbox.setRange(0, 9999)
        spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinbox.setStyleSheet("background-color: #2b2b2b; color: white; border: 1px solid #d4af37;")
        return spinbox

    def setEditorData(self, editor, index):
        if index.column() != 4:
            super().setEditorData(editor, index)
            return
            
        value = index.data(AlchemyModel.CordsRole)
        if value is None: value = 0
        editor.setValue(int(value))

    def setModelData(self, editor, model, index):
        if index.column() != 4:
            super().setModelData(editor, model, index)
            return
            
        value = editor.value()
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
