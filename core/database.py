import sqlite3
import datetime

class DatabaseManager:
    """
    Clase que maneja toda la comunicación con la base de datos SQLite.
    """
    def __init__(self, db_name="panaderia.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.create_tables()

    def create_tables(self):
        """Crea las tablas necesarias si no existen."""
        cursor = self.conn.cursor()
        try:
            # --- Tabla de Productos ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id_prod INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                precio REAL NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,
                produccion_dia INTEGER NOT NULL DEFAULT 0,
                vendido_dia INTEGER NOT NULL DEFAULT 0,
                es_gaseosa BOOLEAN NOT NULL DEFAULT 0,
                oculto BOOLEAN NOT NULL DEFAULT 0
            )
            """)

            # --- Tabla de Trabajadores ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trabajadores (
                id_trab INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT,
                cargo TEXT,
                salario_semanal REAL NOT NULL DEFAULT 0,
                activo BOOLEAN NOT NULL DEFAULT 1
            )
            """)

            # --- Tabla de Proveedores ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id_prov INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT,
                producto_suministrado TEXT,
                pago_mensual REAL NOT NULL DEFAULT 0,
                activo BOOLEAN NOT NULL DEFAULT 1
            )
            """)
            
            # --- Tabla de Ventas ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                id_producto INTEGER NOT NULL,
                nombre_producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                monto_total REAL NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_producto) REFERENCES productos (id_prod)
            )
            """)
            
            # --- Tabla de Pagos (Para trabajadores y proveedores) ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos (
                id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL, -- 'Trabajador' o 'Proveedor'
                id_entidad INTEGER NOT NULL,
                nombre_entidad TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error al crear tablas: {e}")
            self.conn.rollback()

    # --- Métodos de Productos ---

    def add_producto(self, nombre, precio, stock, es_gaseosa):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO productos (nombre, precio, stock, es_gaseosa) 
            VALUES (?, ?, ?, ?)
            """, (nombre, precio, stock, es_gaseosa))
            self.conn.commit()
            return True, "Producto agregado."
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False, "Error: El nombre del producto ya existe."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error de base de datos: {e}"

    def get_productos(self, ver_ocultos=False):
        cursor = self.conn.cursor()
        query = "SELECT * FROM productos"
        if not ver_ocultos:
            query += " WHERE oculto = 0"
        cursor.execute(query)
        # Devolvemos como lista de diccionarios para facilidad en QTableWidget
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]

    def toggle_producto_oculto(self, id_prod):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE productos SET oculto = NOT oculto WHERE id_prod = ?", (id_prod,))
            self.conn.commit()
            return True, "Estado de producto actualizado."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"

    def update_produccion_stock(self, id_prod, cantidad):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            UPDATE productos SET stock = stock + ?, produccion_dia = produccion_dia + ? 
            WHERE id_prod = ?
            """, (cantidad, cantidad, id_prod))
            self.conn.commit()
            return True, "Producción registrada."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"

    def registrar_venta(self, id_prod, cantidad):
        cursor = self.conn.cursor()
        try:
            # 1. Verificar stock
            cursor.execute("SELECT nombre, precio, stock FROM productos WHERE id_prod = ?", (id_prod,))
            producto = cursor.fetchone()
            if not producto:
                return False, "Producto no encontrado."
            
            nombre, precio, stock = producto
            if stock < cantidad:
                return False, f"Stock insuficiente. Stock actual: {stock}"

            # 2. Actualizar stock y vendido_dia
            nuevo_stock = stock - cantidad
            monto_total = precio * cantidad
            cursor.execute("""
            UPDATE productos SET stock = ?, vendido_dia = vendido_dia + ? 
            WHERE id_prod = ?
            """, (nuevo_stock, cantidad, id_prod))

            # 3. Registrar la venta
            cursor.execute("""
            INSERT INTO ventas (id_producto, nombre_producto, cantidad, monto_total) 
            VALUES (?, ?, ?, ?)
            """, (id_prod, nombre, cantidad, monto_total))
            
            self.conn.commit()
            return True, f"Venta registrada. Total: ${monto_total:.2f}"
            
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error en la transacción: {e}"

    def reset_contadores_diarios(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE productos SET produccion_dia = 0, vendido_dia = 0")
            self.conn.commit()
            return True, "Contadores diarios reiniciados."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"

    def get_ventas_semana(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT SUM(monto_total) FROM ventas 
        WHERE fecha >= date('now', '-7 days')
        """)
        resultado = cursor.fetchone()[0]
        return resultado if resultado else 0

    def get_pagos_semana(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT SUM(monto) FROM pagos
        WHERE fecha >= date('now', '-7 days')
        """)
        resultado = cursor.fetchone()[0]
        return resultado if resultado else 0

    # --- Métodos de Trabajadores ---

    def add_trabajador(self, nombre, contacto, cargo, salario):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO trabajadores (nombre, contacto, cargo, salario_semanal) 
            VALUES (?, ?, ?, ?)
            """, (nombre, contacto, cargo, salario))
            self.conn.commit()
            return True, "Trabajador agregado."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"

    def get_trabajadores(self, ver_inactivos=False):
        cursor = self.conn.cursor()
        query = "SELECT * FROM trabajadores"
        if not ver_inactivos:
            query += " WHERE activo = 1"
        cursor.execute(query)
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]

    def toggle_trabajador_activo(self, id_trab):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE trabajadores SET activo = NOT activo WHERE id_trab = ?", (id_trab,))
            self.conn.commit()
            return True, "Estado de trabajador actualizado."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"

    def registrar_pago_trabajador(self, id_trab, nombre, monto):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO pagos (tipo, id_entidad, nombre_entidad, monto) 
            VALUES ('Trabajador', ?, ?, ?)
            """, (id_trab, nombre, monto))
            self.conn.commit()
            return True, f"Pago de ${monto} registrado a {nombre}."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"

    # --- Métodos de Proveedores ---

    def add_proveedor(self, nombre, contacto, producto_suministrado, pago_mensual):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO proveedores (nombre, contacto, producto_suministrado, pago_mensual) 
            VALUES (?, ?, ?, ?)
            """, (nombre, contacto, producto_suministrado, pago_mensual))
            self.conn.commit()
            return True, "Proveedor agregado."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"
            
    def get_proveedores(self, ver_inactivos=False):
        cursor = self.conn.cursor()
        query = "SELECT * FROM proveedores"
        if not ver_inactivos:
            query += " WHERE activo = 1"
        cursor.execute(query)
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]

    def toggle_proveedor_activo(self, id_prov):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE proveedores SET activo = NOT activo WHERE id_prov = ?", (id_prov,))
            self.conn.commit()
            return True, "Estado de proveedor actualizado."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"
            
    def registrar_pago_proveedor(self, id_prov, nombre, monto):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO pagos (tipo, id_entidad, nombre_entidad, monto) 
            VALUES ('Proveedor', ?, ?, ?)
            """, (id_prov, nombre, monto))
            self.conn.commit()
            return True, f"Pago de ${monto} registrado a {nombre}."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"
            
    # --- Métodos de Reportes ---
    def get_datos_reporte_ventas(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_venta, fecha, nombre_producto, cantidad, monto_total FROM ventas ORDER BY fecha DESC")
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]

    def get_datos_grafico_ventas(self):
        cursor = self.conn.cursor()
        # Agrupar ventas por día
        cursor.execute("""
        SELECT date(fecha) as dia, SUM(monto_total) as total_dia
        FROM ventas
        WHERE fecha >= date('now', '-30 days')
        GROUP BY dia
        ORDER BY dia ASC
        """)
        return cursor.fetchall()
        
    def close(self):
        self.conn.close()