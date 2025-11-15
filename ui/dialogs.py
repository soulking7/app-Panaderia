from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox, QComboBox,
    QDoubleSpinBox, QFormLayout, QScrollArea, QWidget
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

class PagoDialog(QDialog):
    """Diálogo para registrar un pago a un trabajador."""
# ... (código existente sin cambios) ...
    def __init__(self, nombre_trabajador, salario_sugerido, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Registrar Pago a {nombre_trabajador}")
        
        self.layout = QFormLayout(self)
        
        self.combo_tipo_pago = QComboBox()
        self.combo_tipo_pago.addItems(["Salario", "Bono/Horas Extra", "Aguinaldo"])
        
        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0.01, 99999.99)
        self.spin_monto.setValue(salario_sugerido)
        
        self.layout.addRow("Tipo de Pago:", self.combo_tipo_pago)
        self.layout.addRow(f"Monto (Sugerido: ${salario_sugerido:.2f}):", self.spin_monto)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.layout.addRow(self.buttons)

    def get_values(self):
# ... (código existente sin cambios) ...
        return {
            "monto": self.spin_monto.value(),
            "tipo_pago": self.combo_tipo_pago.currentText()
        }

class CierreDialog(QDialog):
    """Diálogo para ingresar el conteo final de stock."""
# ... (código existente sin cambios) ...
    def __init__(self, productos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Realizar Cierre de Día - Conteo Final")
        self.setMinimumWidth(400)
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        # Guardamos los spinboxes para leerlos luego
        self.spinboxes = {} 

        widget_interno = QWidget()
        form_layout = QFormLayout(widget_interno)
        
        for prod in productos:
            id_prod = prod['id_prod']
            nombre = prod['nombre']
            stock_actual = prod['stock']
            
            label = QLabel(f"{nombre} (Actual: {stock_actual}):")
            spinbox = QSpinBox()
            spinbox.setRange(0, 9999)
            spinbox.setValue(stock_actual) # Sugerir el stock actual
            
            form_layout.addRow(label, spinbox)
            self.spinboxes[id_prod] = spinbox
            
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget_interno)
        
        self.layout.addWidget(QLabel("Ingrese el conteo de STOCK FINAL de cada producto:"))
        self.layout.addWidget(scroll)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.layout.addWidget(self.buttons)

    def get_conteo_final(self):
# ... (código existente sin cambios) ...
        conteo = {}
        for id_prod, spinbox in self.spinboxes.items():
            conteo[id_prod] = spinbox.value()
        return conteo