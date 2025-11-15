import sqlite3
import datetime

class DatabaseManager:
    """
    Clase que maneja toda la comunicación con la base de datos SQLite.
    Versión 2.0 con Cierre Diario Automático.
    """
    def __init__(self, db_name="panaderia.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.create_tables()

    def create_tables(self):
        """Crea las tablas necesarias si no existen."""
        cursor = self.conn.cursor()
        try:
            # --- Tabla de Productos (sin cambios en estructura) ---
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

            # --- Tabla de Trabajadores (MODIFICADA) ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trabajadores (
                id_trab INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT,
                cargo TEXT,
                salario_semanal REAL NOT NULL DEFAULT 0,
                activo BOOLEAN NOT NULL DEFAULT 1,
                tipo_pago TEXT NOT NULL DEFAULT 'Semanal' 
            )
            """)
            # Intentar añadir la columna tipo_pago si no existe (para migraciones)
            try:
                cursor.execute("ALTER TABLE trabajadores ADD COLUMN tipo_pago TEXT NOT NULL DEFAULT 'Semanal'")
            except sqlite3.OperationalError:
                pass # La columna ya existe

            # --- Tabla de Proveedores (sin cambios) ---
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
            
            # --- Tabla de Ventas (ELIMINADA) ---
            # Esta tabla ya no se usa, la reemplaza 'cierre_diario'
            # cursor.execute("DROP TABLE IF EXISTS ventas")
            
            # --- Tabla de Pagos (MODIFICADA) ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos (
                id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL, -- 'Trabajador' o 'Proveedor'
                id_entidad INTEGER NOT NULL,
                nombre_entidad TEXT NOT NULL,
                monto REAL NOT NULL,
                tipo_pago_realizado TEXT NOT NULL DEFAULT 'Salario', -- Salario, Bono, Aguinaldo
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            try:
                cursor.execute("ALTER TABLE pagos ADD COLUMN tipo_pago_realizado TEXT NOT NULL DEFAULT 'Salario'")
            except sqlite3.OperationalError:
                pass # La columna ya existe

            # --- NUEVA TABLA: Cierre Diario ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cierre_diario (
                id_cierre INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                id_producto INTEGER NOT NULL,
                nombre_producto TEXT NOT NULL,
                stock_inicial INTEGER NOT NULL,
                produccion_dia INTEGER NOT NULL,
                stock_final_conteo INTEGER NOT NULL,
                ventas_calculadas INTEGER NOT NULL,
                ingresos_calculados REAL NOT NULL,
                UNIQUE(fecha, id_producto)
            )
            """)
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error al crear tablas: {e}")
            self.conn.rollback()

    # --- Métodos de Productos (sin cambios) ---
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
        # Esta función ahora solo registra producción, no compra de gaseosas
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            UPDATE productos SET stock = stock + ?, produccion_dia = produccion_dia + ? 
            WHERE id_prod = ? AND es_gaseosa = 0
            """, (cantidad, cantidad, id_prod))
            
            # Gaseosas se compran, no se producen
            cursor.execute("""
            UPDATE productos SET stock = stock + ?
            WHERE id_prod = ? AND es_gaseosa = 1
            """, (cantidad, id_prod))
            
            self.conn.commit()
            return True, "Producción/Compra registrada."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"

    # --- LÓGICA DE CIERRE (NUEVO) ---

    def realizar_cierre_diario(self, fecha, conteo_final):
        """
        Calcula las ventas basado en el conteo final y guarda el cierre.
        'conteo_final' es un diccionario: {id_prod: cantidad_contada}
        """
        cursor = self.conn.cursor()
        try:
            productos = self.get_productos(ver_ocultos=True)
            
            for prod in productos:
                id_prod = prod['id_prod']
                
                # Si el producto no está en el conteo, se asume 0
                stock_final_conteo = conteo_final.get(id_prod, 0) 
                
                # Stock_inicial = stock_actual - produccion_hoy
                # (Asumimos que 'stock' es el stock antes del conteo)
                stock_inicial_dia = prod['stock'] - prod['produccion_dia']
                produccion_dia = prod['produccion_dia']
                
                stock_disponible = stock_inicial_dia + produccion_dia
                
                # Ventas = Disponible - Contado
                ventas_calculadas = stock_disponible - stock_final_conteo
                
                # Evitar ventas negativas si el conteo es mayor (ej. error)
                if ventas_calculadas < 0:
                    ventas_calculadas = 0 
                    
                ingresos_calculados = ventas_calculadas * prod['precio']

                # Insertar o reemplazar el cierre de este producto para este día
                cursor.execute("""
                INSERT INTO cierre_diario (fecha, id_producto, nombre_producto, stock_inicial, produccion_dia, stock_final_conteo, ventas_calculadas, ingresos_calculados)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fecha, id_producto) DO UPDATE SET
                    stock_inicial=excluded.stock_inicial,
                    produccion_dia=excluded.produccion_dia,
                    stock_final_conteo=excluded.stock_final_conteo,
                    ventas_calculadas=excluded.ventas_calculadas,
                    ingresos_calculados=excluded.ingresos_calculados
                """, (fecha, id_prod, prod['nombre'], stock_inicial_dia, produccion_dia, stock_final_conteo, ventas_calculadas, ingresos_calculados))
                
                # Actualizar el stock principal del producto al conteo final
                # Y reiniciar contadores diarios
                cursor.execute("""
                UPDATE productos SET stock = ?, produccion_dia = 0, vendido_dia = 0 
                WHERE id_prod = ?
                """, (stock_final_conteo, id_prod))

            self.conn.commit()
            return True, f"Cierre del {fecha} realizado con éxito."
            
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error en el cierre: {e}"
            
    def get_cierres_por_rango(self, fecha_inicio, fecha_fin):
        """Obtiene los datos de cierre agrupados por producto y fecha."""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT fecha, nombre_producto, stock_inicial, produccion_dia, stock_final_conteo, ventas_calculadas, ingresos_calculados
        FROM cierre_diario
        WHERE fecha BETWEEN ? AND ?
        ORDER BY fecha DESC, nombre_producto ASC
        """, (fecha_inicio, fecha_fin))
        
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]

    def get_ingresos_calculados_semana(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT SUM(ingresos_calculados) FROM cierre_diario
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

    # --- Métodos de Trabajadores (MODIFICADOS) ---

    def add_trabajador(self, nombre, contacto, cargo, salario, tipo_pago):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO trabajadores (nombre, contacto, cargo, salario_semanal, tipo_pago) 
            VALUES (?, ?, ?, ?, ?)
            """, (nombre, contacto, cargo, salario, tipo_pago))
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

    def registrar_pago_trabajador(self, id_trab, nombre, monto, tipo_pago_realizado):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO pagos (tipo, id_entidad, nombre_entidad, monto, tipo_pago_realizado) 
            VALUES ('Trabajador', ?, ?, ?, ?)
            """, (id_trab, nombre, monto, tipo_pago_realizado))
            self.conn.commit()
            return True, f"Pago de ${monto} ({tipo_pago_realizado}) registrado a {nombre}."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"

    # --- Métodos de Proveedores (Sin cambios) ---

    def add_proveedor(self, nombre, contacto, producto_suministrado, pago_mensual):
# ... (código existente sin cambios) ...
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
# ... (código existente sin cambios) ...
        cursor = self.conn.cursor()
        query = "SELECT * FROM proveedores"
        if not ver_inactivos:
            query += " WHERE activo = 1"
        cursor.execute(query)
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]

    def toggle_proveedor_activo(self, id_prov):
# ... (código existente sin cambios) ...
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
            # Modificado para incluir el nuevo tipo de pago
            cursor.execute("""
            INSERT INTO pagos (tipo, id_entidad, nombre_entidad, monto, tipo_pago_realizado) 
            VALUES ('Proveedor', ?, ?, ?, 'Factura')
            """, (id_prov, nombre, monto))
            self.conn.commit()
            return True, f"Pago de ${monto} registrado a {nombre}."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error: {e}"
            
    # --- Métodos de Reportes (MODIFICADOS) ---
    def get_datos_reporte_ventas(self):
        # Ahora exporta desde 'cierre_diario'
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT fecha, nombre_producto, stock_inicial, produccion_dia, stock_final_conteo, ventas_calculadas, ingresos_calculados
        FROM cierre_diario ORDER BY fecha DESC
        """)
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]

    def get_datos_grafico_ventas(self):
        cursor = self.conn.cursor()
        # Agrupar ingresos por día
        cursor.execute("""
        SELECT fecha as dia, SUM(ingresos_calculados) as total_dia
        FROM cierre_diario
        WHERE fecha >= date('now', '-30 days')
        GROUP BY dia
        ORDER BY dia ASC
        """)
        return cursor.fetchall()
        
    def close(self):
        self.conn.close()