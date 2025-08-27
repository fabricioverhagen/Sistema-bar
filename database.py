# database.py - Configuración y manejo de la base de datos
import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="bar_pos.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Inicializa la base de datos con todas las tablas necesarias"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de categorías
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                activo INTEGER DEFAULT 1
            )
        ''')
        
        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio DECIMAL(10,2) NOT NULL,
                categoria_id INTEGER,
                stock INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )
        ''')
        
        # Tabla de mesas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero INTEGER NOT NULL UNIQUE,
                capacidad INTEGER DEFAULT 4,
                estado TEXT DEFAULT 'libre' -- libre, ocupada, reservada
            )
        ''')
        
        # Tabla de mozos/usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo TEXT DEFAULT 'mozo', -- mozo, cajero, admin
                activo INTEGER DEFAULT 1
            )
        ''')
        
        # Tabla de pedidos/órdenes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mesa_id INTEGER,
                usuario_id INTEGER,
                fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                total DECIMAL(10,2) DEFAULT 0,
                estado TEXT DEFAULT 'abierto', -- abierto, finalizado, cancelado
                tipo_venta TEXT DEFAULT 'mesa', -- mesa, caja
                metodo_pago TEXT, -- efectivo, tarjeta, transferencia
                FOREIGN KEY (mesa_id) REFERENCES mesas (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabla de detalles de pedidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedido_detalles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER,
                producto_id INTEGER,
                cantidad INTEGER NOT NULL,
                precio_unitario DECIMAL(10,2) NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insertar datos iniciales si no existen
        self.insert_initial_data()
    
    def insert_initial_data(self):
        """Inserta datos iniciales para pruebas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) FROM categorias")
        if cursor.fetchone()[0] == 0:
            # Insertar categorías
            categorias = [
                ("Bebidas",),
                ("Comidas",),
                ("Postres",),
                ("Entradas",)
            ]
            cursor.executemany("INSERT INTO categorias (nombre) VALUES (?)", categorias)
            
            # Insertar productos
            productos = [
                ("Cerveza Quilmes", 1500, 1, 50),
                ("Fernet con Coca", 2000, 1, 30),
                ("Agua Mineral", 800, 1, 40),
                ("Hamburguesa Completa", 3500, 2, 20),
                ("Papas Fritas", 1800, 2, 25),
                ("Milanesa Napolitana", 4000, 2, 15),
                ("Helado", 1200, 3, 20),
                ("Flan", 1000, 3, 15),
                ("Rabas", 2200, 4, 18),
                ("Empanadas (6u)", 2500, 4, 30)
            ]
            cursor.executemany(
                "INSERT INTO productos (nombre, precio, categoria_id, stock) VALUES (?, ?, ?, ?)", 
                productos
            )
            
            # Insertar mesas
            mesas = [(i, 4) for i in range(1, 16)]  # 15 mesas
            cursor.executemany("INSERT INTO mesas (numero, capacidad) VALUES (?, ?)", mesas)
            
            # Insertar usuarios
            usuarios = [
                ("Juan Pérez", "mozo"),
                ("María García", "mozo"),
                ("Carlos López", "cajero"),
                ("Admin", "admin")
            ]
            cursor.executemany("INSERT INTO usuarios (nombre, tipo) VALUES (?, ?)", usuarios)
        
        conn.commit()
        conn.close()
    
    # Métodos para productos
    def get_productos_por_categoria(self, categoria_id=None):
        """Obtiene productos filtrados por categoría"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if categoria_id:
            cursor.execute('''
                SELECT p.id, p.nombre, p.precio, p.stock, c.nombre as categoria
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.categoria_id = ? AND p.activo = 1
                ORDER BY p.nombre
            ''', (categoria_id,))
        else:
            cursor.execute('''
                SELECT p.id, p.nombre, p.precio, p.stock, c.nombre as categoria
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.activo = 1
                ORDER BY c.nombre, p.nombre
            ''')
        
        productos = cursor.fetchall()
        conn.close()
        return productos
    
    def get_categorias(self):
        """Obtiene todas las categorías activas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM categorias WHERE activo = 1 ORDER BY nombre")
        categorias = cursor.fetchall()
        conn.close()
        return categorias
    
    # Métodos para mesas
    def get_mesas(self):
        """Obtiene todas las mesas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, numero, capacidad, estado FROM mesas ORDER BY numero")
        mesas = cursor.fetchall()
        conn.close()
        return mesas
    
    def cambiar_estado_mesa(self, mesa_id, nuevo_estado):
        """Cambia el estado de una mesa"""
        if nuevo_estado not in ['libre', 'ocupada', 'reservada']:
            raise ValueError("Estado de mesa no válido")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE mesas SET estado = ? WHERE id = ?", (nuevo_estado, mesa_id))
        conn.commit()
        conn.close()
    
    # Métodos para usuarios
    def get_usuarios(self):
        """Obtiene todos los usuarios activos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, tipo FROM usuarios WHERE activo = 1 ORDER BY nombre")
        usuarios = cursor.fetchall()
        conn.close()
        return usuarios
    
    # Métodos para pedidos
    def crear_pedido(self, mesa_id, usuario_id, tipo_venta="mesa"):
        """Crea un nuevo pedido"""
        if tipo_venta not in ['mesa', 'caja']:
            raise ValueError("Tipo de venta no válido")
        
        # Verificar que no haya un pedido abierto para la mesa
        if mesa_id and tipo_venta == "mesa":
            pedido_existente = self.get_pedido_activo_mesa(mesa_id)
            if pedido_existente:
                return pedido_existente[0]  # Retornar el pedido existente
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pedidos (mesa_id, usuario_id, tipo_venta, fecha_hora)
            VALUES (?, ?, ?, ?)
        ''', (mesa_id, usuario_id, tipo_venta, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        pedido_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Si es una mesa, cambiar estado a ocupada
        if tipo_venta == "mesa" and mesa_id:
            self.cambiar_estado_mesa(mesa_id, "ocupada")
        
        return pedido_id
    
    def agregar_producto_pedido(self, pedido_id, producto_id, cantidad):
        """Agrega un producto al pedido"""
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar que el pedido existe y está abierto
        cursor.execute("SELECT estado FROM pedidos WHERE id = ?", (pedido_id,))
        pedido = cursor.fetchone()
        if not pedido or pedido[0] != 'abierto':
            raise ValueError("El pedido no existe o ya está cerrado")
        
        # Obtener precio del producto
        cursor.execute("SELECT precio FROM productos WHERE id = ? AND activo = 1", (producto_id,))
        producto = cursor.fetchone()
        if not producto:
            raise ValueError("El producto no existe o no está activo")
        
        precio = producto[0]
        subtotal = precio * cantidad
        
        # Verificar si el producto ya existe en el pedido
        cursor.execute('''
            SELECT id, cantidad FROM pedido_detalles 
            WHERE pedido_id = ? AND producto_id = ?
        ''', (pedido_id, producto_id))
        
        detalle_existente = cursor.fetchone()
        
        if detalle_existente:
            # Actualizar cantidad existente
            nueva_cantidad = detalle_existente[1] + cantidad
            nuevo_subtotal = precio * nueva_cantidad
            cursor.execute('''
                UPDATE pedido_detalles 
                SET cantidad = ?, subtotal = ?
                WHERE id = ?
            ''', (nueva_cantidad, nuevo_subtotal, detalle_existente[0]))
        else:
            # Insertar nuevo detalle
            cursor.execute('''
                INSERT INTO pedido_detalles (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            ''', (pedido_id, producto_id, cantidad, precio, subtotal))
        
        # Actualizar total del pedido
        cursor.execute('''
            UPDATE pedidos SET total = (
                SELECT SUM(subtotal) FROM pedido_detalles WHERE pedido_id = ?
            ) WHERE id = ?
        ''', (pedido_id, pedido_id))
        
        conn.commit()
        conn.close()
    
    def get_pedido_activo_mesa(self, mesa_id):
        """Obtiene el pedido activo de una mesa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, total FROM pedidos 
            WHERE mesa_id = ? AND estado = 'abierto'
            ORDER BY fecha_hora DESC LIMIT 1
        ''', (mesa_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_detalles_pedido(self, pedido_id):
        """Obtiene los detalles de un pedido"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pd.id, p.nombre, pd.cantidad, pd.precio_unitario, pd.subtotal
            FROM pedido_detalles pd
            JOIN productos p ON pd.producto_id = p.id
            WHERE pd.pedido_id = ?
            ORDER BY p.nombre
        ''', (pedido_id,))
        detalles = cursor.fetchall()
        conn.close()
        return detalles
    
    def eliminar_detalle_pedido(self, detalle_id):
        """Elimina un detalle del pedido"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Obtener pedido_id antes de eliminar
        cursor.execute("SELECT pedido_id FROM pedido_detalles WHERE id = ?", (detalle_id,))
        result = cursor.fetchone()
        if not result:
            raise ValueError("El detalle del pedido no existe")
        
        pedido_id = result[0]
        
        # Verificar que el pedido está abierto
        cursor.execute("SELECT estado FROM pedidos WHERE id = ?", (pedido_id,))
        pedido = cursor.fetchone()
        if not pedido or pedido[0] != 'abierto':
            raise ValueError("No se puede modificar un pedido cerrado")
        
        # Eliminar detalle
        cursor.execute("DELETE FROM pedido_detalles WHERE id = ?", (detalle_id,))
        
        # Actualizar total del pedido
        cursor.execute('''
            UPDATE pedidos SET total = COALESCE((
                SELECT SUM(subtotal) FROM pedido_detalles WHERE pedido_id = ?
            ), 0) WHERE id = ?
        ''', (pedido_id, pedido_id))
        
        conn.commit()
        conn.close()
    
    def finalizar_pedido(self, pedido_id, metodo_pago):
        """Finaliza un pedido"""
        if metodo_pago not in ['efectivo', 'tarjeta', 'transferencia']:
            raise ValueError("Método de pago no válido")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Obtener información del pedido
        cursor.execute("SELECT mesa_id, estado FROM pedidos WHERE id = ?", (pedido_id,))
        result = cursor.fetchone()
        
        if not result:
            raise ValueError("El pedido no existe")
        
        if result[1] != 'abierto':
            raise ValueError("El pedido ya está finalizado")
        
        mesa_id = result[0]
        
        # Verificar que el pedido tiene productos
        cursor.execute("SELECT COUNT(*) FROM pedido_detalles WHERE pedido_id = ?", (pedido_id,))
        if cursor.fetchone()[0] == 0:
            raise ValueError("No se puede finalizar un pedido sin productos")
        
        # Actualizar pedido
        cursor.execute('''
            UPDATE pedidos 
            SET estado = 'finalizado', metodo_pago = ?
            WHERE id = ?
        ''', (metodo_pago, pedido_id))
        
        # Liberar mesa si es venta en mesa
        if mesa_id:
            self.cambiar_estado_mesa(mesa_id, "libre")
        
        conn.commit()
        conn.close()
    
    def get_pedido_completo(self, pedido_id):
        """Obtiene información completa del pedido para facturación"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Información del pedido
        cursor.execute('''
            SELECT p.id, p.fecha_hora, p.total, p.metodo_pago, p.tipo_venta,
                   m.numero as mesa_numero, u.nombre as usuario_nombre
            FROM pedidos p
            LEFT JOIN mesas m ON p.mesa_id = m.id
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE p.id = ?
        ''', (pedido_id,))
        
        pedido_info = cursor.fetchone()
        
        if not pedido_info:
            conn.close()
            return None
        
        # Detalles del pedido
        cursor.execute('''
            SELECT pd.cantidad, pd.precio_unitario, pd.subtotal, pr.nombre
            FROM pedido_detalles pd
            JOIN productos pr ON pd.producto_id = pr.id
            WHERE pd.pedido_id = ?
            ORDER BY pr.nombre
        ''', (pedido_id,))
        
        detalles = cursor.fetchall()
        conn.close()
        
        return {
            'pedido': pedido_info,
            'detalles': detalles
        }
    
    def cancelar_pedido(self, pedido_id):
        """Cancela un pedido abierto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Obtener información del pedido
        cursor.execute("SELECT mesa_id, estado FROM pedidos WHERE id = ?", (pedido_id,))
        result = cursor.fetchone()
        
        if not result:
            raise ValueError("El pedido no existe")
        
        if result[1] != 'abierto':
            raise ValueError("Solo se pueden cancelar pedidos abiertos")
        
        mesa_id = result[0]
        
        # Cancelar pedido
        cursor.execute("UPDATE pedidos SET estado = 'cancelado' WHERE id = ?", (pedido_id,))
        
        # Liberar mesa si es venta en mesa
        if mesa_id:
            self.cambiar_estado_mesa(mesa_id, "libre")
        
        conn.commit()
        conn.close()

# Función para crear instancia global de la base de datos
def get_db():
    return DatabaseManager()