from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox
    )


class InputDialog(QDialog):
    """Diálogo simple para pedir una cantidad."""
    def __init__(self, parent=None, titulo="Ingresar Valor", etiqueta="Cantidad:"):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel(etiqueta)
        self.spinbox = QSpinBox(self)
        self.spinbox.setRange(1, 9999)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spinbox)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.layout.addWidget(self.buttons)

    def get_value(self):
        return self.spinbox.value()
    
