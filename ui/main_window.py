import sys
import os
import datetime

# --- Importaciones de PyQt6 ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
    QDoubleSpinBox, QSpinBox, QCheckBox, QHBoxLayout, QLabel, QHeaderView,
    QDialog, QDialogButtonBox, QStyle
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon # Importar QIcon

# --- Importaciones para Reportes ---
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    REPORTES_ENABLED = True
except ImportError:
    REPORTES_ENABLED = False
    print("Advertencia: 'pandas', 'openpyxl' o 'matplotlib' no están instalados.")
    print("Las funciones de exportar a Excel y generar gráficos estarán desactivadas.")
    print("Instálalos con: pip install pandas openpyxl matplotlib")

# --- Importar nuestro propio código ---
from core.database import DatabaseManager
from .dialogs import InputDialog # El . significa "desde esta misma carpeta (ui)"


# --- 4. INTERFAZ GRÁFICA PRINCIPAL (PYQT6) ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Panadería (POO + PyQt6 + SQLite)")
        self.setGeometry(100, 100, 1000, 700)
        
        # Conectar a la base de datos
        self.db = DatabaseManager()
        
        # --- Configuración del Widget de Pestañas ---
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # --- Crear Pestañas ---
        self.tab_ventas = QWidget()
        self.tab_stock = QWidget()
        self.tab_personal = QWidget()
        self.tab_proveedores = QWidget()
        self.tab_reportes = QWidget()
        
        self.tab_widget.addTab(self.tab_ventas, "Ventas y Caja")
        self.tab_widget.addTab(self.tab_stock, "Productos y Stock")
        self.tab_widget.addTab(self.tab_personal, "Personal")
        self.tab_widget.addTab(self.tab_proveedores, "Proveedores")
        self.tab_widget.addTab(self.tab_reportes, "Reportes y Cierre")
        
        # --- Inicializar el contenido de cada pestaña ---
        self.init_ventas_ui()
        self.init_stock_ui()
        self.init_personal_ui()
        self.init_proveedores_ui()
        self.init_reportes_ui()

        # Cargar datos iniciales
        self.refresh_combobox_productos()
        self.refresh_table_productos()
        self.refresh_table_trabajadores()
        self.refresh_table_proveedores()

    def init_ventas_ui(self):
        layout = QVBoxLayout(self.tab_ventas)
        
        # --- Formulario de Registro de Venta ---
        form_venta = QFormLayout()
        self.venta_combo_producto = QComboBox()
        self.venta_spin_cantidad = QSpinBox()
        self.venta_spin_cantidad.setRange(1, 999)
        
        form_venta.addRow("Producto:", self.venta_combo_producto)
        form_venta.addRow("Cantidad:", self.venta_spin_cantidad)
        
        self.btn_registrar_venta = QPushButton(" Registrar Venta")
        # --- ICONO CORREGIDO ---
        icon_venta = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)
        self.btn_registrar_venta.setIcon(QIcon(icon_venta))
        # --- FIN ICONO ---
        self.btn_registrar_venta.clicked.connect(self.slot_registrar_venta)
        
        layout.addLayout(form_venta)
        layout.addWidget(self.btn_registrar_venta)
        
        # --- Cuadre de Caja Semanal ---
        caja_layout = QVBoxLayout()
        self.label_ingresos_semana = QLabel("Ingresos (7 días): $0.00")
        self.label_pagos_semana = QLabel("Pagos (7 días): $0.00")
        self.label_balance_semana = QLabel("Balance (7 días): $0.00")
        
        # Estilizar etiquetas de balance
        font = self.label_ingresos_semana.font()
        font.setPointSize(14)
        self.label_ingresos_semana.setFont(font)
        self.label_pagos_semana.setFont(font)
        self.label_balance_semana.setFont(font)
        
        self.btn_cuadrar_caja = QPushButton(" Calcular Cuadre de Caja Semanal")
        # --- ICONO CORREGIDO ---
        icon_caja = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        self.btn_cuadrar_caja.setIcon(QIcon(icon_caja))
        # --- FIN ICONO ---
        self.btn_cuadrar_caja.clicked.connect(self.slot_cuadrar_caja)
        
        caja_layout.addWidget(QLabel("--- CUADRE DE CAJA SEMANAL ---"))
        caja_layout.addWidget(self.label_ingresos_semana)
        caja_layout.addWidget(self.label_pagos_semana)
        caja_layout.addWidget(self.label_balance_semana)
        caja_layout.addWidget(self.btn_cuadrar_caja)
        
        layout.addLayout(caja_layout)
        layout.addStretch() # Empuja todo hacia arriba

    def init_stock_ui(self):
        main_layout = QHBoxLayout(self.tab_stock)
        
        # --- Columna Izquierda: Formularios ---
        form_col = QVBoxLayout()
        
        # Formulario de Nuevo Producto
        form_nuevo = QFormLayout()
        form_nuevo.setContentsMargins(10, 10, 10, 10)
        self.stock_entry_nombre = QLineEdit()
        self.stock_spin_precio = QDoubleSpinBox()
        self.stock_spin_precio.setRange(0.01, 9999.99)
        self.stock_spin_stock_inicial = QSpinBox()
        self.stock_spin_stock_inicial.setRange(0, 9999)
        self.stock_check_gaseosa = QCheckBox("¿Es Gaseosa?")
        
        form_nuevo.addRow("Nombre:", self.stock_entry_nombre)
        form_nuevo.addRow("Precio:", self.stock_spin_precio)
        form_nuevo.addRow("Stock Inicial:", self.stock_spin_stock_inicial)
        form_nuevo.addRow(self.stock_check_gaseosa)
        
        self.btn_agregar_producto = QPushButton(" Agregar Nuevo Producto")
        # --- ICONO CORREGIDO (ListAdd no existe, usamos Apply) ---
        icon_add = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_agregar_producto.setIcon(QIcon(icon_add))
        # --- FIN ICONO ---
        self.btn_agregar_producto.clicked.connect(self.slot_agregar_producto)
        
        form_col.addWidget(QLabel("--- Agregar Producto ---"))
        form_col.addLayout(form_nuevo)
        form_col.addWidget(self.btn_agregar_producto)
        form_col.addSpacing(20)

        # Formulario de Registrar Producción
        form_prod = QFormLayout()
        form_prod.setContentsMargins(10, 10, 10, 10)
        self.stock_combo_producto_prod = QComboBox() # Otro combo para producción
        
        form_prod.addRow("Producto:", self.stock_combo_producto_prod)
        
        self.btn_add_produccion = QPushButton(" Registrar Producción/Compra")
        # --- ICONO CORREGIDO ---
        icon_prod = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)
        self.btn_add_produccion.setIcon(QIcon(icon_prod))
        # --- FIN ICONO ---
        self.btn_add_produccion.clicked.connect(self.slot_agregar_produccion)
        
        form_col.addWidget(QLabel("--- Registrar Producción / Compra de Stock ---"))
        form_col.addLayout(form_prod)
        form_col.addWidget(self.btn_add_produccion)
        form_col.addStretch()

        # --- Columna Derecha: Tabla ---
        table_col = QVBoxLayout()
        
        self.stock_check_ver_ocultos = QCheckBox("Ver productos ocultos")
        self.stock_check_ver_ocultos.stateChanged.connect(self.refresh_table_productos)
        
        self.table_productos = QTableWidget()
        self.table_productos_headers = ["ID", "Nombre", "Precio", "Stock", "Prod. Hoy", "Vend. Hoy", "Gaseosa", "Oculto"]
        self.table_productos.setColumnCount(len(self.table_productos_headers))
        self.table_productos.setHorizontalHeaderLabels(self.table_productos_headers)
        self.table_productos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_productos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_productos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.btn_toggle_oculto_prod = QPushButton(" Ocultar/Mostrar Seleccionado")
        # --- ICONO CORREGIDO ---
        icon_hide = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        self.btn_toggle_oculto_prod.setIcon(QIcon(icon_hide))
        # --- FIN ICONO ---
        self.btn_toggle_oculto_prod.clicked.connect(self.slot_toggle_producto)
        
        table_col.addWidget(self.stock_check_ver_ocultos)
        table_col.addWidget(self.table_productos)
        table_col.addWidget(self.btn_toggle_oculto_prod)

        main_layout.addLayout(form_col, 1) # 1/3 del espacio
        main_layout.addLayout(table_col, 2) # 2/3 del espacio

    def init_personal_ui(self):
        main_layout = QHBoxLayout(self.tab_personal)
        
        # --- Columna Izquierda: Formularios ---
        form_col = QVBoxLayout()
        
        # Formulario de Nuevo Trabajador
        form_nuevo = QFormLayout()
        form_nuevo.setContentsMargins(10, 10, 10, 10)
        self.personal_entry_nombre = QLineEdit()
        self.personal_entry_contacto = QLineEdit()
        self.personal_entry_cargo = QLineEdit()
        self.personal_spin_salario = QDoubleSpinBox()
        self.personal_spin_salario.setRange(0.00, 99999.99)
        
        form_nuevo.addRow("Nombre:", self.personal_entry_nombre)
        form_nuevo.addRow("Contacto (Tel/Email):", self.personal_entry_contacto)
        form_nuevo.addRow("Cargo:", self.personal_entry_cargo)
        form_nuevo.addRow("Salario Semanal:", self.personal_spin_salario)
        
        self.btn_agregar_trabajador = QPushButton(" Agregar Trabajador")
        # --- ICONO CORREGIDO (ListAdd no existe, usamos Apply) ---
        icon_add_user = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_agregar_trabajador.setIcon(QIcon(icon_add_user))
        # --- FIN ICONO ---
        self.btn_agregar_trabajador.clicked.connect(self.slot_agregar_trabajador)
        
        form_col.addWidget(QLabel("--- Agregar Personal ---"))
        form_col.addLayout(form_nuevo)
        form_col.addWidget(self.btn_agregar_trabajador)
        form_col.addStretch()

        # --- Columna Derecha: Tabla ---
        table_col = QVBoxLayout()
        
        self.personal_check_ver_inactivos = QCheckBox("Ver personal inactivo (archivado)")
        self.personal_check_ver_inactivos.stateChanged.connect(self.refresh_table_trabajadores)
        
        self.table_trabajadores = QTableWidget()
        self.table_trabajadores_headers = ["ID", "Nombre", "Contacto", "Cargo", "Salario Semanal", "Activo"]
        self.table_trabajadores.setColumnCount(len(self.table_trabajadores_headers))
        self.table_trabajadores.setHorizontalHeaderLabels(self.table_trabajadores_headers)
        self.table_trabajadores.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_trabajadores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_trabajadores.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        btn_layout = QHBoxLayout()
        self.btn_toggle_activo_trab = QPushButton(" Archivar/Reactivar Seleccionado")
        # --- ICONO CORREGIDO ---
        icon_archive_user = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        self.btn_toggle_activo_trab.setIcon(QIcon(icon_archive_user))
        # --- FIN ICONO ---
        self.btn_toggle_activo_trab.clicked.connect(self.slot_toggle_trabajador)
        
        self.btn_pagar_trabajador = QPushButton(" Registrar Pago a Seleccionado")
        # --- ICONO CORREGIDO ---
        icon_pay = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_pagar_trabajador.setIcon(QIcon(icon_pay))
        # --- FIN ICONO ---
        self.btn_pagar_trabajador.clicked.connect(self.slot_pagar_trabajador)
        
        btn_layout.addWidget(self.btn_toggle_activo_trab)
        btn_layout.addWidget(self.btn_pagar_trabajador)
        
        table_col.addWidget(self.personal_check_ver_inactivos)
        table_col.addWidget(self.table_trabajadores)
        table_col.addLayout(btn_layout)

        main_layout.addLayout(form_col, 1)
        main_layout.addLayout(table_col, 2)

    def init_proveedores_ui(self):
        main_layout = QHBoxLayout(self.tab_proveedores)
        
        # --- Columna Izquierda: Formularios ---
        form_col = QVBoxLayout()
        
        # Formulario de Nuevo Proveedor
        form_nuevo = QFormLayout()
        form_nuevo.setContentsMargins(10, 10, 10, 10)
        self.prov_entry_nombre = QLineEdit()
        self.prov_entry_contacto = QLineEdit()
        self.prov_entry_producto = QLineEdit()
        self.prov_spin_pago = QDoubleSpinBox()
        self.prov_spin_pago.setRange(0.00, 99999.99)
        
        form_nuevo.addRow("Nombre:", self.prov_entry_nombre)
        form_nuevo.addRow("Contacto (Tel/Email):", self.prov_entry_contacto)
        form_nuevo.addRow("Producto que Suministra:", self.prov_entry_producto)
        form_nuevo.addRow("Pago Mensual (Estimado):", self.prov_spin_pago)
        
        self.btn_agregar_proveedor = QPushButton(" Agregar Proveedor")
        # --- ICONO CORREGIDO (ListAdd no existe, usamos Apply) ---
        icon_add_prov = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_agregar_proveedor.setIcon(QIcon(icon_add_prov))
        # --- FIN ICONO ---
        self.btn_agregar_proveedor.clicked.connect(self.slot_agregar_proveedor)
        
        form_col.addWidget(QLabel("--- Agregar Proveedor ---"))
        form_col.addLayout(form_nuevo)
        form_col.addWidget(self.btn_agregar_proveedor)
        form_col.addStretch()

        # --- Columna Derecha: Tabla ---
        table_col = QVBoxLayout()
        
        self.prov_check_ver_inactivos = QCheckBox("Ver proveedores inactivos (archivados)")
        self.prov_check_ver_inactivos.stateChanged.connect(self.refresh_table_proveedores)
        
        self.table_proveedores = QTableWidget()
        self.table_prov_headers = ["ID", "Nombre", "Contacto", "Suministro", "Pago Mensual", "Activo"]
        self.table_proveedores.setColumnCount(len(self.table_prov_headers))
        self.table_proveedores.setHorizontalHeaderLabels(self.table_prov_headers)
        self.table_proveedores.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_proveedores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_proveedores.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        btn_layout = QHBoxLayout()
        self.btn_toggle_activo_prov = QPushButton(" Archivar/Reactivar Seleccionado")
        # --- ICONO CORREGIDO ---
        icon_archive_prov = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        self.btn_toggle_activo_prov.setIcon(QIcon(icon_archive_prov))
        # --- FIN ICONO ---
        self.btn_toggle_activo_prov.clicked.connect(self.slot_toggle_proveedor)
        
        self.btn_pagar_proveedor = QPushButton(" Registrar Pago a Seleccionado")
        # --- ICONO CORREGIDO ---
        icon_pay_prov = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_pagar_proveedor.setIcon(QIcon(icon_pay_prov))
        # --- FIN ICONO ---
        self.btn_pagar_proveedor.clicked.connect(self.slot_pagar_proveedor)
        
        btn_layout.addWidget(self.btn_toggle_activo_prov)
        btn_layout.addWidget(self.btn_pagar_proveedor)
        
        table_col.addWidget(self.prov_check_ver_inactivos)
        table_col.addWidget(self.table_proveedores)
        table_col.addLayout(btn_layout)

        main_layout.addLayout(form_col, 1)
        main_layout.addLayout(table_col, 2)
        
    def init_reportes_ui(self):
        layout = QVBoxLayout(self.tab_reportes)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Exportación a Excel ---
        layout.addWidget(QLabel("--- Exportar Reportes ---"))
        self.btn_exportar_excel = QPushButton(" Exportar Reporte de Ventas a Excel")
        
        # --- ICONO CORREGIDO (SP_DriveSaveIcon no existe, usamos SP_DialogSaveButton) ---
        icon_excel = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton) 
        self.btn_exportar_excel.setIcon(QIcon(icon_excel))
        # --- FIN ICONO ---
        
        self.btn_exportar_excel.clicked.connect(self.slot_exportar_excel)
        if not REPORTES_ENABLED:
            self.btn_exportar_excel.setDisabled(True)
            self.btn_exportar_excel.setText("Exportar a Excel (Deshabilitado - ver consola)")
        
        layout.addWidget(self.btn_exportar_excel)
        layout.addSpacing(20)

        # --- Gráficos ---
        layout.addWidget(QLabel("--- Gráficos ---"))
        self.btn_generar_grafico = QPushButton(" Generar Gráfico de Ventas (Últimos 30 días)")
        # --- ICONO CORREGIDO ---
        icon_chart = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        self.btn_generar_grafico.setIcon(QIcon(icon_chart))
        # --- FIN ICONO ---
        self.btn_generar_grafico.clicked.connect(self.slot_generar_grafico)
        if not REPORTES_ENABLED:
            self.btn_generar_grafico.setDisabled(True)
            self.btn_generar_grafico.setText("Generar Gráfico (Deshabilitado - ver consola)")
            
        layout.addWidget(self.btn_generar_grafico)
        layout.addSpacing(40)
        
        # --- Cierre Diario ---
        layout.addWidget(QLabel("--- Cierre del Día ---"))
        self.btn_reset_diario = QPushButton(" Reiniciar Contadores Diarios")
        # --- IDENTIFICADOR ÚNICO PARA QSS ---
        self.btn_reset_diario.setObjectName("BtnResetDiario") 
        # --- ICONO CORREGIDO ---
        icon_warn = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        self.btn_reset_diario.setIcon(QIcon(icon_warn))
        # --- FIN ICONO ---
        self.btn_reset_diario.clicked.connect(self.slot_reset_diario)
        layout.addWidget(self.btn_reset_diario)
        
        layout.addStretch()

    # --- SLOTS (Lógica de la Aplicación) ---

    def _show_message(self, titulo, mensaje, tipo="info"):
        """Función helper para mostrar mensajes."""
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle(titulo)
        msgBox.setText(mensaje)
        if tipo == "info":
            msgBox.setIcon(QMessageBox.Icon.Information)
        elif tipo == "error":
            msgBox.setIcon(QMessageBox.Icon.Critical)
        msgBox.exec()

    # --- Slots de Ventas y Caja ---
    
    def slot_registrar_venta(self):
        try:
            id_prod = self.venta_combo_producto.currentData()
            cantidad = self.venta_spin_cantidad.value()
            
            if not id_prod or cantidad <= 0:
                self._show_message("Error", "Seleccione un producto y una cantidad válida.", "error")
                return
                
            success, message = self.db.registrar_venta(id_prod, cantidad)
            
            if success:
                self._show_message("Éxito", message)
                self.venta_spin_cantidad.setValue(1)
                self.refresh_table_productos() # Actualizar stock en la otra pestaña
            else:
                self._show_message("Error de Venta", message, "error")
        except Exception as e:
            self._show_message("Error", f"Ocurrió un error inesperado: {e}", "error")

    def slot_cuadrar_caja(self):
        ingresos = self.db.get_ventas_semana()
        pagos = self.db.get_pagos_semana()
        balance = ingresos - pagos
        
        self.label_ingresos_semana.setText(f"Ingresos (7 días): ${ingresos:.2f}")
        self.label_pagos_semana.setText(f"Pagos (7 días): ${pagos:.2f}")
        self.label_balance_semana.setText(f"Balance (7 días): ${balance:.2f}")
        
        self._show_message("Cuadre de Caja Semanal",
                           f"Ingresos: ${ingresos:.2f}\n"
                           f"Pagos: ${pagos:.2f}\n"
                           f"-------------------\n"
                           f"Balance: ${balance:.2f}")

    # --- Slots de Productos y Stock ---
    
    def refresh_combobox_productos(self):
        """Recarga los combobox de productos en Pestaña Ventas y Pestaña Stock."""
        productos = self.db.get_productos(ver_ocultos=False)
        
        self.venta_combo_producto.clear()
        self.stock_combo_producto_prod.clear()
        
        if not productos:
            self.venta_combo_producto.addItem("No hay productos disponibles")
            self.stock_combo_producto_prod.addItem("No hay productos disponibles")
            return
            
        for prod in productos:
            texto = f"{prod['nombre']} (Stock: {prod['stock']})"
            self.venta_combo_producto.addItem(texto, prod['id_prod'])
            self.stock_combo_producto_prod.addItem(texto, prod['id_prod'])

    def refresh_table_productos(self):
        ver_ocultos = self.stock_check_ver_ocultos.isChecked()
        productos = self.db.get_productos(ver_ocultos)
        
        self.table_productos.setRowCount(0) # Limpiar tabla
        for i, prod in enumerate(productos):
            self.table_productos.insertRow(i)
            self.table_productos.setItem(i, 0, QTableWidgetItem(str(prod['id_prod'])))
            self.table_productos.setItem(i, 1, QTableWidgetItem(prod['nombre']))
            self.table_productos.setItem(i, 2, QTableWidgetItem(f"${prod['precio']:.2f}"))
            self.table_productos.setItem(i, 3, QTableWidgetItem(str(prod['stock'])))
            self.table_productos.setItem(i, 4, QTableWidgetItem(str(prod['produccion_dia'])))
            self.table_productos.setItem(i, 5, QTableWidgetItem(str(prod['vendido_dia'])))
            self.table_productos.setItem(i, 6, QTableWidgetItem("Sí" if prod['es_gaseosa'] else "No"))
            self.table_productos.setItem(i, 7, QTableWidgetItem("Sí" if prod['oculto'] else "No"))
        
        # Ocultar la columna ID (es útil tenerla pero no verla)
        self.table_productos.setColumnHidden(0, True)

    def slot_agregar_producto(self):
        nombre = self.stock_entry_nombre.text()
        precio = self.stock_spin_precio.value()
        stock = self.stock_spin_stock_inicial.value()
        es_gaseosa = self.stock_check_gaseosa.isChecked()
        
        if not nombre or precio <= 0:
            self._show_message("Error", "Nombre y Precio son obligatorios.", "error")
            return
        
        success, message = self.db.add_producto(nombre, precio, stock, es_gaseosa)
        
        if success:
            self._show_message("Éxito", message)
            # Limpiar formulario
            self.stock_entry_nombre.clear()
            self.stock_spin_precio.setValue(0.01)
            self.stock_spin_stock_inicial.setValue(0)
            self.stock_check_gaseosa.setChecked(False)
            # Actualizar vistas
            self.refresh_table_productos()
            self.refresh_combobox_productos()
        else:
            self._show_message("Error al Guardar", message, "error")

    def slot_agregar_produccion(self):
        id_prod = self.stock_combo_producto_prod.currentData()
        if not id_prod:
            self._show_message("Error", "Seleccione un producto.", "error")
            return
        
        dialog = InputDialog(self, "Registrar Producción/Compra", "Cantidad a agregar:")
        if dialog.exec():
            cantidad = dialog.get_value()
            success, message = self.db.update_produccion_stock(id_prod, cantidad)
            if success:
                self._show_message("Éxito", message)
                self.refresh_table_productos()
                self.refresh_combobox_productos()
            else:
                self._show_message("Error", message, "error")

    def _get_selected_id(self, tabla):
        """Helper para obtener el ID de la fila seleccionada."""
        selected_rows = tabla.selectionModel().selectedRows()
        if not selected_rows:
            self._show_message("Error", "No ha seleccionado ninguna fila.", "error")
            return None
        
        # El ID está en la columna 0 (oculta)
        id_item = tabla.item(selected_rows[0].row(), 0)
        return int(id_item.text())

    def slot_toggle_producto(self):
        id_prod = self._get_selected_id(self.table_productos)
        if id_prod:
            success, message = self.db.toggle_producto_oculto(id_prod)
            if success:
                self.refresh_table_productos()
                self.refresh_combobox_productos()
            else:
                self._show_message("Error", message, "error")

    # --- Slots de Personal ---
    
    def refresh_table_trabajadores(self):
        ver_inactivos = self.personal_check_ver_inactivos.isChecked()
        trabajadores = self.db.get_trabajadores(ver_inactivos)
        
        self.table_trabajadores.setRowCount(0)
        for i, trab in enumerate(trabajadores):
            self.table_trabajadores.insertRow(i)
            self.table_trabajadores.setItem(i, 0, QTableWidgetItem(str(trab['id_trab'])))
            self.table_trabajadores.setItem(i, 1, QTableWidgetItem(trab['nombre']))
            self.table_trabajadores.setItem(i, 2, QTableWidgetItem(trab['contacto']))
            self.table_trabajadores.setItem(i, 3, QTableWidgetItem(trab['cargo']))
            self.table_trabajadores.setItem(i, 4, QTableWidgetItem(f"${trab['salario_semanal']:.2f}"))
            self.table_trabajadores.setItem(i, 5, QTableWidgetItem("Sí" if trab['activo'] else "No"))
        
        self.table_trabajadores.setColumnHidden(0, True)

    def slot_agregar_trabajador(self):
        nombre = self.personal_entry_nombre.text()
        contacto = self.personal_entry_contacto.text()
        cargo = self.personal_entry_cargo.text()
        salario = self.personal_spin_salario.value()
        
        if not nombre:
            self._show_message("Error", "El nombre es obligatorio.", "error")
            return
            
        success, message = self.db.add_trabajador(nombre, contacto, cargo, salario)
        if success:
            self._show_message("Éxito", message)
            self.personal_entry_nombre.clear()
            self.personal_entry_contacto.clear()
            self.personal_entry_cargo.clear()
            self.personal_spin_salario.setValue(0)
            self.refresh_table_trabajadores()
        else:
            self._show_message("Error", message, "error")

    def slot_toggle_trabajador(self):
        id_trab = self._get_selected_id(self.table_trabajadores)
        if id_trab:
            success, message = self.db.toggle_trabajador_activo(id_trab)
            if success:
                self.refresh_table_trabajadores()
            else:
                self._show_message("Error", message, "error")

    def slot_pagar_trabajador(self):
        id_trab = self._get_selected_id(self.table_trabajadores)
        if not id_trab:
            return
            
        # Obtener nombre y salario de la tabla para el diálogo
        row = self.table_trabajadores.selectionModel().selectedRows()[0].row()
        nombre = self.table_trabajadores.item(row, 1).text()
        salario_str = self.table_trabajadores.item(row, 4).text().replace("$", "")
        salario = float(salario_str)

        dialog = InputDialog(self, f"Pagar a {nombre}", f"Monto a Pagar (Sugerido: ${salario:.2f}):")
        dialog.spinbox.setRange(1, 99999)
        dialog.spinbox.setValue(int(salario)) # Usamos int para el spinbox
        
        if dialog.exec():
            monto = dialog.get_value()
            success, message = self.db.registrar_pago_trabajador(id_trab, nombre, monto)
            if success:
                self._show_message("Éxito", message)
            else:
                self._show_message("Error", message, "error")

    # --- Slots de Proveedores ---

    def refresh_table_proveedores(self):
        ver_inactivos = self.prov_check_ver_inactivos.isChecked()
        proveedores = self.db.get_proveedores(ver_inactivos)
        
        self.table_proveedores.setRowCount(0)
        for i, prov in enumerate(proveedores):
            self.table_proveedores.insertRow(i)
            self.table_proveedores.setItem(i, 0, QTableWidgetItem(str(prov['id_prov'])))
            self.table_proveedores.setItem(i, 1, QTableWidgetItem(prov['nombre']))
            self.table_proveedores.setItem(i, 2, QTableWidgetItem(prov['contacto']))
            self.table_proveedores.setItem(i, 3, QTableWidgetItem(prov['producto_suministrado']))
            self.table_proveedores.setItem(i, 4, QTableWidgetItem(f"${prov['pago_mensual']:.2f}"))
            self.table_proveedores.setItem(i, 5, QTableWidgetItem("Sí" if prov['activo'] else "No"))
        
        self.table_proveedores.setColumnHidden(0, True)

    def slot_agregar_proveedor(self):
        nombre = self.prov_entry_nombre.text()
        contacto = self.prov_entry_contacto.text()
        producto = self.prov_entry_producto.text()
        pago = self.prov_spin_pago.value()
        
        if not nombre:
            self._show_message("Error", "El nombre es obligatorio.", "error")
            return
            
        success, message = self.db.add_proveedor(nombre, contacto, producto, pago)
        if success:
            self._show_message("Éxito", message)
            self.prov_entry_nombre.clear()
            self.prov_entry_contacto.clear()
            self.prov_entry_producto.clear()
            self.prov_spin_pago.setValue(0)
            self.refresh_table_proveedores()
        else:
            self._show_message("Error", message, "error")

    def slot_toggle_proveedor(self):
        id_prov = self._get_selected_id(self.table_proveedores)
        if id_prov:
            success, message = self.db.toggle_proveedor_activo(id_prov)
            if success:
                self.refresh_table_proveedores()
            else:
                self._show_message("Error", message, "error")
                
    def slot_pagar_proveedor(self):
        id_prov = self._get_selected_id(self.table_proveedores)
        if not id_prov:
            return
            
        row = self.table_proveedores.selectionModel().selectedRows()[0].row()
        nombre = self.table_proveedores.item(row, 1).text()

        dialog = InputDialog(self, f"Pagar a {nombre}", "Monto a Pagar:")
        
        if dialog.exec():
            monto = dialog.get_value()
            success, message = self.db.registrar_pago_proveedor(id_prov, nombre, monto)
            if success:
                self._show_message("Éxito", message)
            else:
                self._show_message("Error", message, "error")

    # --- Slots de Reportes y Cierre ---
    
    def slot_exportar_excel(self):
        if not REPORTES_ENABLED:
            self._show_message("Error", "Bibliotecas de reportes no instaladas.", "error")
            return
        
        datos = self.db.get_datos_reporte_ventas()
        if not datos:
            self._show_message("Info", "No hay ventas para exportar.")
            return

        try:
            df = pd.DataFrame(datos)
            # Formatear la fecha para que sea más legible en Excel
            df['fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Guardar el archivo
            archivo_excel = "reporte_ventas_panaderia.xlsx"
            df.to_excel(archivo_excel, index=False, sheet_name="Ventas")
            
            self._show_message("Éxito", f"Reporte guardado como '{archivo_excel}'\n"
                                        f"El archivo se encuentra en:\n{os.path.abspath(archivo_excel)}")
        except Exception as e:
            self._show_message("Error de Exportación", f"No se pudo guardar el archivo Excel.\nError: {e}", "error")

    def slot_generar_grafico(self):
        if not REPORTES_ENABLED:
            self._show_message("Error", "Bibliotecas de gráficos no instaladas.", "error")
            return
        
        datos = self.db.get_datos_grafico_ventas()
        if not datos:
            self._show_message("Info", "No hay datos de ventas suficientes para generar un gráfico.")
            return

        # Desempaquetar datos para matplotlib
        dias = [fila[0] for fila in datos]
        totales = [fila[1] for fila in datos]

        try:
            plt.figure(figsize=(10, 6))
            plt.bar(dias, totales, color='skyblue')
            plt.xlabel("Fecha")
            plt.ylabel("Total Ventas ($)")
            plt.title("Ventas Totales por Día (Últimos 30 días)")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show() # Muestra el gráfico en una nueva ventana
            
        except Exception as e:
            self._show_message("Error de Gráfico", f"No se pudo generar el gráfico.\nError: {e}", "error")
            
    def slot_reset_diario(self):
        confirm = QMessageBox.question(self, "Confirmar Cierre Diario",
                                       "¿Está seguro de que desea reiniciar los contadores de 'Producción Hoy' y 'Vendido Hoy' a CERO?\n\n"
                                       "Esta acción es irreversible y debe hacerse al final del día.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.db.reset_contadores_diarios()
            if success:
                self._show_message("Cierre Diario", message)
                self.refresh_table_productos()
            else:
                self._show_message("Error", message, "error")

    def closeEvent(self, event):
        """Sobrescribe el evento de cierre para cerrar la DB."""
        self.db.close()
        print("Conexión a la base de datos cerrada.")
        event.accept()
        