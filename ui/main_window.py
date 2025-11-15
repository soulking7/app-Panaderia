import sys
import os
import datetime

# --- Importaciones de PyQt6 ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
    QDoubleSpinBox, QSpinBox, QCheckBox, QHBoxLayout, QLabel, QHeaderView,
    QDialog, QDialogButtonBox, QStyle, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon 

# --- Importaciones para Reportes ---
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    REPORTES_ENABLED = True
except ImportError:
    REPORTES_ENABLED = False
    print("Advertencia: 'pandas', 'openpyxl' o 'matplotlib' no están instalados.")

# --- Importar nuestro propio código ---
from core.database import DatabaseManager
# Importamos TODOS los diálogos
from .dialogs import PagoDialog, CierreDialog, InputDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Panadería (v2.1 - Pago Proveedor)")
        self.setGeometry(100, 100, 1000, 700)
        
        self.db = DatabaseManager()
        
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # --- Pestañas ---
        self.tab_cierres = QWidget() # Pestaña de Ventas ahora es Cierres
        self.tab_stock = QWidget()
        self.tab_personal = QWidget()
        self.tab_proveedores = QWidget()
        self.tab_reportes = QWidget()
        
        self.tab_widget.addTab(self.tab_cierres, "Cierres y Caja") # Renombrada
        self.tab_widget.addTab(self.tab_stock, "Productos y Stock")
        self.tab_widget.addTab(self.tab_personal, "Personal")
        self.tab_widget.addTab(self.tab_proveedores, "Proveedores")
        self.tab_widget.addTab(self.tab_reportes, "Ejecutar Cierre y Reportes") # Renombrada
        
        # --- Inicializar ---
        self.init_cierres_ui() # Nueva pestaña de cierres
        self.init_stock_ui()
        self.init_personal_ui() # Modificada
        self.init_proveedores_ui() # Modificada
        self.init_reportes_ui() # Modificada

        # Cargar datos iniciales
        self.refresh_combobox_productos()
        self.refresh_table_productos()
        self.refresh_table_trabajadores()
        self.refresh_table_proveedores()

    # --- PESTAÑA 1: CIERRES Y CAJA (ANTES VENTAS) ---
    def init_cierres_ui(self):
        layout = QVBoxLayout(self.tab_cierres)
        
        # --- Selector de Fechas ---
        date_layout = QHBoxLayout()
        self.date_inicio = QDateEdit()
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setDate(QDate.currentDate().addDays(-7))
        
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        
        self.btn_buscar_cierres = QPushButton(" Buscar Cierres")
        icon_buscar = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        self.btn_buscar_cierres.setIcon(QIcon(icon_buscar))
        self.btn_buscar_cierres.clicked.connect(self.slot_buscar_cierres)
        
        date_layout.addWidget(QLabel("Desde:"))
        date_layout.addWidget(self.date_inicio)
        date_layout.addWidget(QLabel("Hasta:"))
        date_layout.addWidget(self.date_fin)
        date_layout.addWidget(self.btn_buscar_cierres)
        date_layout.addStretch()

        layout.addLayout(date_layout)

        # --- Tabla de Cierres ---
        self.table_cierres = QTableWidget()
        self.table_cierres_headers = ["Fecha", "Producto", "Stock Inicial", "Producción", "Stock Final", "Ventas (calc)", "Ingresos (calc)"]
        self.table_cierres.setColumnCount(len(self.table_cierres_headers))
        self.table_cierres.setHorizontalHeaderLabels(self.table_cierres_headers)
        self.table_cierres.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_cierres.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_cierres.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table_cierres)

        # --- Cuadre de Caja Semanal ---
        caja_layout = QVBoxLayout()
        self.label_ingresos_semana = QLabel("Ingresos (7 días): $0.00")
        self.label_pagos_semana = QLabel("Pagos (7 días): $0.00")
        self.label_balance_semana = QLabel("Balance (7 días): $0.00")
        
        font = self.label_ingresos_semana.font()
        font.setPointSize(14)
        self.label_ingresos_semana.setFont(font)
        self.label_pagos_semana.setFont(font)
        self.label_balance_semana.setFont(font)
        
        self.btn_cuadrar_caja = QPushButton(" Calcular Cuadre de Caja Semanal")
        icon_caja = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        self.btn_cuadrar_caja.setIcon(QIcon(icon_caja))
        self.btn_cuadrar_caja.clicked.connect(self.slot_cuadrar_caja)
        
        caja_layout.addWidget(QLabel("--- CUADRE DE CAJA SEMANAL ---"))
        caja_layout.addWidget(self.label_ingresos_semana)
        caja_layout.addWidget(self.label_pagos_semana)
        caja_layout.addWidget(self.label_balance_semana)
        caja_layout.addWidget(self.btn_cuadrar_caja)
        
        layout.addLayout(caja_layout)

    # --- PESTAÑA 2: STOCK (Sin cambios lógicos) ---
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
        icon_add = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_agregar_producto.setIcon(QIcon(icon_add))
        self.btn_agregar_producto.clicked.connect(self.slot_agregar_producto)
        
        form_col.addWidget(QLabel("--- Agregar Producto ---"))
        form_col.addLayout(form_nuevo)
        form_col.addWidget(self.btn_agregar_producto)
        form_col.addSpacing(20)

        # Formulario de Registrar Producción
        form_prod = QFormLayout()
        form_prod.setContentsMargins(10, 10, 10, 10)
        self.stock_combo_producto_prod = QComboBox() 
        
        form_prod.addRow("Producto (Pan o Gaseosa):", self.stock_combo_producto_prod)
        
        self.btn_add_produccion = QPushButton(" Registrar Producción/Compra")
        icon_prod = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)
        self.btn_add_produccion.setIcon(QIcon(icon_prod))
        self.btn_add_produccion.clicked.connect(self.slot_agregar_produccion)
        
        form_col.addWidget(QLabel("--- Registrar Producción (Panes) / Compra (Gaseosas) ---"))
        form_col.addLayout(form_prod)
        form_col.addWidget(self.btn_add_produccion)
        form_col.addStretch()

        # --- Columna Derecha: Tabla ---
        table_col = QVBoxLayout()
        
        self.stock_check_ver_ocultos = QCheckBox("Ver productos ocultos")
        self.stock_check_ver_ocultos.stateChanged.connect(self.refresh_table_productos)
        
        self.table_productos = QTableWidget()
        self.table_productos_headers = ["ID", "Nombre", "Precio", "Stock Actual", "Prod. Hoy", "Gaseosa", "Oculto"]
        self.table_productos.setColumnCount(len(self.table_productos_headers))
        self.table_productos.setHorizontalHeaderLabels(self.table_productos_headers)
        self.table_productos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_productos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_productos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.btn_toggle_oculto_prod = QPushButton(" Ocultar/Mostrar Seleccionado")
        icon_hide = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        self.btn_toggle_oculto_prod.setIcon(QIcon(icon_hide))
        self.btn_toggle_oculto_prod.clicked.connect(self.slot_toggle_producto)
        
        table_col.addWidget(self.stock_check_ver_ocultos)
        table_col.addWidget(self.table_productos)
        table_col.addWidget(self.btn_toggle_oculto_prod)

        main_layout.addLayout(form_col, 1) 
        main_layout.addLayout(table_col, 2) 

    # --- PESTAÑA 3: PERSONAL (MODIFICADA) ---
    def init_personal_ui(self):
        main_layout = QHBoxLayout(self.tab_personal)
        
        # --- Columna Izquierda: Formularios ---
        form_col = QVBoxLayout()
        
        form_nuevo = QFormLayout()
        form_nuevo.setContentsMargins(10, 10, 10, 10)
        self.personal_entry_nombre = QLineEdit()
        self.personal_entry_contacto = QLineEdit()
        self.personal_entry_cargo = QLineEdit()
        
        # Tipo de Pago (Nuevo)
        self.personal_combo_tipo_pago = QComboBox()
        self.personal_combo_tipo_pago.addItems(["Semanal", "Diario"])
        
        self.personal_spin_salario = QDoubleSpinBox()
        self.personal_spin_salario.setRange(0.00, 99999.99)
        
        form_nuevo.addRow("Nombre:", self.personal_entry_nombre)
        form_nuevo.addRow("Contacto (Tel/Email):", self.personal_entry_contacto)
        form_nuevo.addRow("Cargo:", self.personal_entry_cargo)
        form_nuevo.addRow("Tipo de Pago:", self.personal_combo_tipo_pago) # Nuevo
        form_nuevo.addRow("Salario (por tipo):", self.personal_spin_salario) # Modificado
        
        self.btn_agregar_trabajador = QPushButton(" Agregar Trabajador")
        icon_add_user = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_agregar_trabajador.setIcon(QIcon(icon_add_user))
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
        # Cabeceras Modificadas
        self.table_trabajadores_headers = ["ID", "Nombre", "Contacto", "Cargo", "Tipo Pago", "Salario", "Activo"]
        self.table_trabajadores.setColumnCount(len(self.table_trabajadores_headers))
        self.table_trabajadores.setHorizontalHeaderLabels(self.table_trabajadores_headers)
        self.table_trabajadores.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_trabajadores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_trabajadores.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        btn_layout = QHBoxLayout()
        self.btn_toggle_activo_trab = QPushButton(" Archivar/Reactivar Seleccionado")
        icon_archive_user = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        self.btn_toggle_activo_trab.setIcon(QIcon(icon_archive_user))
        self.btn_toggle_activo_trab.clicked.connect(self.slot_toggle_trabajador)
        
        self.btn_pagar_trabajador = QPushButton(" Registrar Pago (Salario, Bono, Aguinaldo)") # Modificado
        icon_pay = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_pagar_trabajador.setIcon(QIcon(icon_pay))
        self.btn_pagar_trabajador.clicked.connect(self.slot_pagar_trabajador) # Lógica Modificada
        
        btn_layout.addWidget(self.btn_toggle_activo_trab)
        btn_layout.addWidget(self.btn_pagar_trabajador)
        
        table_col.addWidget(self.personal_check_ver_inactivos)
        table_col.addWidget(self.table_trabajadores)
        table_col.addLayout(btn_layout)

        main_layout.addLayout(form_col, 1)
        main_layout.addLayout(table_col, 2)

    # --- PESTAÑA 4: PROVEEDORES (MODIFICADA) ---
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
        # CAMBIO: Eliminado self.prov_spin_pago
        
        form_nuevo.addRow("Nombre:", self.prov_entry_nombre)
        form_nuevo.addRow("Contacto (Tel/Email):", self.prov_entry_contacto)
        form_nuevo.addRow("Producto que Suministra:", self.prov_entry_producto)
        # CAMBIO: Eliminada fila de "Pago Mensual"
        
        self.btn_agregar_proveedor = QPushButton(" Agregar Proveedor")
        icon_add_prov = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_agregar_proveedor.setIcon(QIcon(icon_add_prov))
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
        # CAMBIO: Eliminada columna "Pago Mensual"
        self.table_prov_headers = ["ID", "Nombre", "Contacto", "Suministro", "Activo"]
        self.table_proveedores.setColumnCount(len(self.table_prov_headers)) # Ajustado a 5
        self.table_proveedores.setHorizontalHeaderLabels(self.table_prov_headers)
        self.table_proveedores.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_proveedores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_proveedores.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        btn_layout = QHBoxLayout()
        self.btn_toggle_activo_prov = QPushButton(" Archivar/Reactivar Seleccionado")
        icon_archive_prov = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        self.btn_toggle_activo_prov.setIcon(QIcon(icon_archive_prov))
        self.btn_toggle_activo_prov.clicked.connect(self.slot_toggle_proveedor)
        
        # CAMBIO: Texto del botón ajustado
        self.btn_pagar_proveedor = QPushButton(" Registrar Pago (Factura)")
        icon_pay_prov = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.btn_pagar_proveedor.setIcon(QIcon(icon_pay_prov))
        self.btn_pagar_proveedor.clicked.connect(self.slot_pagar_proveedor)
        
        btn_layout.addWidget(self.btn_toggle_activo_prov)
        btn_layout.addWidget(self.btn_pagar_proveedor)
        
        table_col.addWidget(self.prov_check_ver_inactivos)
        table_col.addWidget(self.table_proveedores)
        table_col.addLayout(btn_layout)

        main_layout.addLayout(form_col, 1)
        main_layout.addLayout(table_col, 2)
        
    # --- PESTAÑA 5: REPORTES Y CIERRE (MODIFICADA) ---
    def init_reportes_ui(self):
        layout = QVBoxLayout(self.tab_reportes)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Cierre Diario (NUEVA LÓGICA) ---
        layout.addWidget(QLabel("--- Cierre del Día ---"))
        self.btn_ejecutar_cierre = QPushButton(" Ejecutar Cierre de Día (Contar Stock)")
        self.btn_ejecutar_cierre.setObjectName("BtnResetDiario") # Mantiene el estilo rojo
        icon_warn = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        self.btn_ejecutar_cierre.setIcon(QIcon(icon_warn))
        self.btn_ejecutar_cierre.clicked.connect(self.slot_ejecutar_cierre) # Nuevo Slot
        layout.addWidget(self.btn_ejecutar_cierre)
        layout.addSpacing(40)
        
        # --- Exportación a Excel ---
        layout.addWidget(QLabel("--- Exportar Reportes ---"))
        self.btn_exportar_excel = QPushButton(" Exportar Reporte de CIERRES a Excel")
        icon_excel = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton) 
        self.btn_exportar_excel.setIcon(QIcon(icon_excel))
        self.btn_exportar_excel.clicked.connect(self.slot_exportar_excel) # Modificado
        if not REPORTES_ENABLED:
            self.btn_exportar_excel.setDisabled(True)
        
        layout.addWidget(self.btn_exportar_excel)
        layout.addSpacing(20)

        # --- Gráficos ---
        layout.addWidget(QLabel("--- Gráficos ---"))
        self.btn_generar_grafico = QPushButton(" Generar Gráfico de INGRESOS (Últimos 30 días)")
        icon_chart = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        self.btn_generar_grafico.setIcon(QIcon(icon_chart))
        self.btn_generar_grafico.clicked.connect(self.slot_generar_grafico) # Modificado
        if not REPORTES_ENABLED:
            self.btn_generar_grafico.setDisabled(True)
            
        layout.addWidget(self.btn_generar_grafico)
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

    # --- Slots de Cierres y Caja (NUEVOS) ---
    
    def slot_buscar_cierres(self):
        fecha_inicio = self.date_inicio.date().toString("yyyy-MM-dd")
        fecha_fin = self.date_fin.date().toString("yyyy-MM-dd")
        
        cierres = self.db.get_cierres_por_rango(fecha_inicio, fecha_fin)
        
        self.table_cierres.setRowCount(0)
        for i, cierre in enumerate(cierres):
            self.table_cierres.insertRow(i)
            self.table_cierres.setItem(i, 0, QTableWidgetItem(cierre['fecha']))
            self.table_cierres.setItem(i, 1, QTableWidgetItem(cierre['nombre_producto']))
            self.table_cierres.setItem(i, 2, QTableWidgetItem(str(cierre['stock_inicial'])))
            self.table_cierres.setItem(i, 3, QTableWidgetItem(str(cierre['produccion_dia'])))
            self.table_cierres.setItem(i, 4, QTableWidgetItem(str(cierre['stock_final_conteo'])))
            self.table_cierres.setItem(i, 5, QTableWidgetItem(str(cierre['ventas_calculadas'])))
            self.table_cierres.setItem(i, 6, QTableWidgetItem(f"${cierre['ingresos_calculados']:.2f}"))

    def slot_cuadrar_caja(self):
        # Ahora usa la nueva función de la DB
        ingresos = self.db.get_ingresos_calculados_semana()
        pagos = self.db.get_pagos_semana()
        balance = ingresos - pagos
        
        self.label_ingresos_semana.setText(f"Ingresos (7 días): ${ingresos:.2f}")
        self.label_pagos_semana.setText(f"Pagos (7 días): ${pagos:.2f}")
        self.label_balance_semana.setText(f"Balance (7 días): ${balance:.2f}")
        
        self._show_message("Cuadre de Caja Semanal",
                           f"Ingresos Calculados: ${ingresos:.2f}\n"
                           f"Pagos Registrados: ${pagos:.2f}\n"
                           f"-------------------\n"
                           f"Balance: ${balance:.2f}")

    # --- Slots de Productos y Stock ---
    
    def refresh_combobox_productos(self):
        """Recarga los combobox de productos en Pestaña Ventas y Pestaña Stock."""
        productos = self.db.get_productos(ver_ocultos=False)
        
        self.stock_combo_producto_prod.clear()
        
        if not productos:
            self.stock_combo_producto_prod.addItem("No hay productos disponibles")
            return
            
        for prod in productos:
            texto = f"{prod['nombre']} (Stock: {prod['stock']})"
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
            # self.table_productos.setItem(i, 5, QTableWidgetItem(str(prod['vendido_dia']))) # Ya no es relevante aquí
            self.table_productos.setItem(i, 5, QTableWidgetItem("Sí" if prod['es_gaseosa'] else "No"))
            self.table_productos.setItem(i, 6, QTableWidgetItem("Sí" if prod['oculto'] else "No"))
        
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
        
        # CAMBIO: Usar el InputDialog importado
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

    # --- Slots de Personal (MODIFICADOS) ---
    
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
            self.table_trabajadores.setItem(i, 4, QTableWidgetItem(trab['tipo_pago'])) # Nuevo
            self.table_trabajadores.setItem(i, 5, QTableWidgetItem(f"${trab['salario_semanal']:.2f}")) # Renombrado
            self.table_trabajadores.setItem(i, 6, QTableWidgetItem("Sí" if trab['activo'] else "No"))
        
        self.table_trabajadores.setColumnHidden(0, True)

    def slot_agregar_trabajador(self):
        nombre = self.personal_entry_nombre.text()
        contacto = self.personal_entry_contacto.text()
        cargo = self.personal_entry_cargo.text()
        salario = self.personal_spin_salario.value()
        tipo_pago = self.personal_combo_tipo_pago.currentText() # Nuevo
        
        if not nombre:
            self._show_message("Error", "El nombre es obligatorio.", "error")
            return
            
        success, message = self.db.add_trabajador(nombre, contacto, cargo, salario, tipo_pago)
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
            
        row = self.table_trabajadores.selectionModel().selectedRows()[0].row()
        nombre = self.table_trabajadores.item(row, 1).text()
        salario_str = self.table_trabajadores.item(row, 5).text().replace("$", "")
        salario = float(salario_str)

        # Usar el nuevo PagoDialog
        dialog = PagoDialog(nombre, salario, self)
        
        if dialog.exec():
            valores = dialog.get_values()
            monto = valores["monto"]
            tipo_pago = valores["tipo_pago"]
            
            success, message = self.db.registrar_pago_trabajador(id_trab, nombre, monto, tipo_pago)
            if success:
                self._show_message("Éxito", message)
            else:
                self._show_message("Error", message, "error")

    # --- Slots de Proveedores (MODIFICADOS) ---

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
            # CAMBIO: La columna 4 ahora es "Activo"
            self.table_proveedores.setItem(i, 4, QTableWidgetItem("Sí" if prov['activo'] else "No"))
        
        self.table_proveedores.setColumnHidden(0, True)

    def slot_agregar_proveedor(self):
        nombre = self.prov_entry_nombre.text()
        contacto = self.prov_entry_contacto.text()
        producto = self.prov_entry_producto.text()
        # CAMBIO: Eliminado 'pago'
        
        if not nombre:
            self._show_message("Error", "El nombre es obligatorio.", "error")
            return
        
        # CAMBIO: Llamada a DB modificada
        success, message = self.db.add_proveedor(nombre, contacto, producto)
        if success:
            self._show_message("Éxito", message)
            self.prov_entry_nombre.clear()
            self.prov_entry_contacto.clear()
            self.prov_entry_producto.clear()
            # CAMBIO: Eliminado spin_pago.setValue(0)
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
        
        # CAMBIO: Usar el InputDialog importado
        dialog = InputDialog(self, f"Pagar a {nombre}", "Monto a Pagar (Factura):")
        dialog.spinbox.setRange(1, 99999) # Establecer rango
        
        if dialog.exec():
            monto = dialog.get_value()
            success, message = self.db.registrar_pago_proveedor(id_prov, nombre, monto)
            if success:
                self._show_message("Éxito", message)
            else:
                self._show_message("Error", message, "error")

    # --- Slots de Reportes y Cierre (MODIFICADOS) ---
    
    def slot_exportar_excel(self):
        if not REPORTES_ENABLED:
            self._show_message("Error", "Bibliotecas de reportes no instaladas.", "error")
            return
        
        datos = self.db.get_datos_reporte_ventas()
        if not datos:
            self._show_message("Info", "No hay datos de cierres para exportar.")
            return

        try:
            df = pd.DataFrame(datos)
            archivo_excel = "reporte_cierres_panaderia.xlsx"
            df.to_excel(archivo_excel, index=False, sheet_name="CierresDiarios")
            
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
            self._show_message("Info", "No hay datos de ingresos suficientes para generar un gráfico.")
            return

        dias = [fila[0] for fila in datos]
        totales = [fila[1] for fila in datos]

        try:
            plt.figure(figsize=(10, 6))
            plt.bar(dias, totales, color='skyblue')
            plt.xlabel("Fecha")
            plt.ylabel("Total Ingresos ($)")
            plt.title("Ingresos Calculados por Día (Últimos 30 días)")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show() 
            
        except Exception as e:
            self._show_message("Error de Gráfico", f"No se pudo generar el gráfico.\nError: {e}", "error")
            
    def slot_ejecutar_cierre(self):
        # NUEVO: Lanza el diálogo de Cierre de Día
        
        # Obtenemos productos (incluyendo gaseosas)
        productos = self.db.get_productos(ver_ocultos=False) 
        if not productos:
            self._show_message("Error", "No hay productos para contar.", "error")
            return

        dialog = CierreDialog(productos, self)
        
        if dialog.exec():
            conteo_final = dialog.get_conteo_final()
            fecha_cierre = datetime.date.today()

            confirm = QMessageBox.question(self, "Confirmar Cierre",
                                       f"¿Está seguro de ejecutar el cierre para la fecha {fecha_cierre}?\n\n"
                                       "Esto calculará las ventas y REEMPLAZARÁ el stock actual con el conteo ingresado.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            
            if confirm == QMessageBox.StandardButton.Yes:
                success, message = self.db.realizar_cierre_diario(fecha_cierre, conteo_final)
                if success:
                    self._show_message("Cierre Diario", message)
                    self.refresh_table_productos()
                    self.refresh_combobox_productos()
                else:
                    self._show_message("Error en Cierre", message, "error")

    def closeEvent(self, event):
        """Sobrescribe el evento de cierre para cerrar la DB."""
        self.db.close()
        print("Conexión a la base de datos cerrada.")
        event.accept()