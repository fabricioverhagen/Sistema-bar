# main.py - Interfaz principal del sistema POS (Versión mejorada)
import tkinter as tk
from tkinter import ttk, messagebox
from database import get_db
import threading
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class POSSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema POS - Bar")
        self.root.geometry("1200x700")
        self.root.configure(bg="#2c3e50")
        
        self.db = get_db()
        self.usuario_actual = None
        self.pedido_actual = None
        self.mesa_actual = None
        
        # Variable para controlar ventana de venta directa
        self.venta_directa_window = None
        
        self.setup_styles()
        self.create_login_screen()
    
    def setup_styles(self):
        """Configura los estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores
        style.configure('Title.TLabel', 
                       font=('Arial', 16, 'bold'),
                       background="#2c3e50",
                       foreground="white")
        
        style.configure('Header.TLabel',
                       font=('Arial', 12, 'bold'),
                       background="#34495e",
                       foreground="white",
                       padding=10)
        
        style.configure('Info.TLabel',
                       font=('Arial', 10),
                       background="#2c3e50",
                       foreground="white")
        
        style.configure('Success.TButton',
                       font=('Arial', 10, 'bold'),
                       padding=5)
    
    def create_login_screen(self):
        """Crea la pantalla de login"""
        self.clear_screen()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(expand=True, fill="both")
        
        # Título
        title_label = tk.Label(main_frame, text="Sistema POS - Bar",
                              font=('Arial', 24, 'bold'),
                              bg="#2c3e50", fg="white")
        title_label.pack(pady=50)
        
        # Frame de login
        login_frame = tk.Frame(main_frame, bg="#34495e", padx=30, pady=30)
        login_frame.pack()
        
        tk.Label(login_frame, text="Seleccionar Usuario:",
                font=('Arial', 12, 'bold'),
                bg="#34495e", fg="white").pack(pady=10)
        
        # Combobox de usuarios
        self.usuario_var = tk.StringVar()
        usuarios = self.db.get_usuarios()
        valores_usuarios = [f"{u[0]} - {u[1]} ({u[2]})" for u in usuarios]
        
        usuario_combo = ttk.Combobox(login_frame, textvariable=self.usuario_var,
                                    values=valores_usuarios, state="readonly",
                                    font=('Arial', 11), width=25)
        usuario_combo.pack(pady=10)
        
        # Botón de login
        login_btn = tk.Button(login_frame, text="Iniciar Sesión",
                             command=self.login, font=('Arial', 12, 'bold'),
                             bg="#3498db", fg="white", padx=20, pady=10)
        login_btn.pack(pady=20)
    
    def login(self):
        """Maneja el proceso de login"""
        if not self.usuario_var.get():
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        try:
            usuario_id = self.usuario_var.get().split(" - ")[0]
            usuarios = self.db.get_usuarios()
            self.usuario_actual = next((u for u in usuarios if str(u[0]) == usuario_id), None)
            
            if self.usuario_actual:
                self.create_main_screen()
            else:
                messagebox.showerror("Error", "Usuario no válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar sesión: {str(e)}")
    
    def create_main_screen(self):
        """Crea la pantalla principal del sistema"""
        self.clear_screen()
        
        # Frame superior con información del usuario
        top_frame = tk.Frame(self.root, bg="#34495e", height=60)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        
        info_frame = tk.Frame(top_frame, bg="#34495e")
        info_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        user_label = tk.Label(info_frame, 
                             text=f"Usuario: {self.usuario_actual[1]} ({self.usuario_actual[2]})",
                             font=('Arial', 12, 'bold'), bg="#34495e", fg="white")
        user_label.pack(side="left")
        
        logout_btn = tk.Button(info_frame, text="Cerrar Sesión",
                              command=self.logout, font=('Arial', 10),
                              bg="#e74c3c", fg="white")
        logout_btn.pack(side="right")
        
        # Frame principal con pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Crear pestañas según el tipo de usuario
        self.create_ventas_tab()
        if self.usuario_actual[2] in ['cajero', 'admin']:
            self.create_caja_tab()
        if self.usuario_actual[2] == 'admin':
            self.create_admin_tab()
    
    def create_ventas_tab(self):
        """Crea la pestaña de ventas en mesa"""
        ventas_frame = ttk.Frame(self.notebook)
        self.notebook.add(ventas_frame, text="Ventas en Mesa")
        
        # Panel izquierdo - Mesas
        left_frame = tk.Frame(ventas_frame, bg="#ecf0f1", width=300)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        left_frame.pack_propagate(False)
        
        tk.Label(left_frame, text="MESAS", font=('Arial', 14, 'bold'),
                bg="#ecf0f1").pack(pady=10)
        
        # Botón para refrescar mesas
        refresh_btn = tk.Button(left_frame, text="🔄 Refrescar",
                               command=self.load_mesas, font=('Arial', 10),
                               bg="#95a5a6", fg="white")
        refresh_btn.pack(pady=5)
        
        # Frame para las mesas
        self.mesas_frame = tk.Frame(left_frame, bg="#ecf0f1")
        self.mesas_frame.pack(expand=True, fill="both", padx=10)
        
        self.load_mesas()
        
        # Panel derecho - Productos y pedido
        right_frame = tk.Frame(ventas_frame, bg="#ecf0f1")
        right_frame.pack(side="right", expand=True, fill="both", padx=5, pady=5)
        
        # Información de mesa actual
        self.mesa_info_frame = tk.Frame(right_frame, bg="#3498db", height=60)
        self.mesa_info_frame.pack(fill="x", pady=(0,10))
        self.mesa_info_frame.pack_propagate(False)
        
        self.mesa_info_label = tk.Label(self.mesa_info_frame, 
                                       text="Seleccione una mesa",
                                       font=('Arial', 14, 'bold'),
                                       bg="#3498db", fg="white")
        self.mesa_info_label.pack(expand=True)
        
        # Frame de contenido principal
        content_frame = tk.Frame(right_frame, bg="#ecf0f1")
        content_frame.pack(expand=True, fill="both")
        
        # Panel de categorías y productos
        productos_frame = tk.Frame(content_frame, bg="#ecf0f1")
        productos_frame.pack(side="left", expand=True, fill="both")
        
        # Categorías
        categorias_frame = tk.Frame(productos_frame, bg="#ecf0f1", height=50)
        categorias_frame.pack(fill="x", pady=(0,10))
        categorias_frame.pack_propagate(False)
        
        tk.Label(categorias_frame, text="Categorías:", font=('Arial', 11, 'bold'),
                bg="#ecf0f1").pack(side="left", padx=5)
        
        self.categoria_var = tk.StringVar()
        categorias = [("0", "Todas")] + self.db.get_categorias()
        
        for cat_id, cat_nombre in categorias:
            btn = tk.Radiobutton(categorias_frame, text=cat_nombre,
                               variable=self.categoria_var, value=cat_id,
                               command=self.load_productos,
                               bg="#ecf0f1", font=('Arial', 10))
            btn.pack(side="left", padx=5)
        
        self.categoria_var.set("0")
        
        # Lista de productos
        self.productos_frame = tk.Frame(productos_frame, bg="#ecf0f1")
        self.productos_frame.pack(expand=True, fill="both")
        
        # Panel del pedido actual
        pedido_frame = tk.Frame(content_frame, bg="#ecf0f1", width=350)
        pedido_frame.pack(side="right", fill="y", padx=(10,0))
        pedido_frame.pack_propagate(False)
        
        tk.Label(pedido_frame, text="PEDIDO ACTUAL", font=('Arial', 12, 'bold'),
                bg="#ecf0f1").pack(pady=10)
        
        # Lista del pedido
        self.pedido_listbox_frame = tk.Frame(pedido_frame, bg="#ecf0f1")
        self.pedido_listbox_frame.pack(expand=True, fill="both", padx=10)
        
        # Total y botones
        self.total_frame = tk.Frame(pedido_frame, bg="#ecf0f1", height=150)
        self.total_frame.pack(fill="x", padx=10, pady=10)
        self.total_frame.pack_propagate(False)
        
        self.total_label = tk.Label(self.total_frame, text="Total: $0.00",
                                   font=('Arial', 14, 'bold'),
                                   bg="#ecf0f1")
        self.total_label.pack()
        
        # Botones de acción
        self.finalizar_btn = tk.Button(self.total_frame, text="Finalizar Pedido",
                                      command=self.finalizar_pedido,
                                      font=('Arial', 11, 'bold'),
                                      bg="#27ae60", fg="white", state="disabled")
        self.finalizar_btn.pack(pady=5, fill="x")
        
        self.cancelar_btn = tk.Button(self.total_frame, text="Cancelar Pedido",
                                     command=self.cancelar_pedido_actual,
                                     font=('Arial', 10),
                                     bg="#e67e22", fg="white", state="disabled")
        self.cancelar_btn.pack(pady=2, fill="x")
        
        self.load_productos()
    
    def create_caja_tab(self):
        """Crea la pestaña de ventas directas en caja"""
        caja_frame = ttk.Frame(self.notebook)
        self.notebook.add(caja_frame, text="Venta Directa")
        
        tk.Label(caja_frame, text="VENTA DIRECTA EN CAJA", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Botón para nueva venta directa
        nueva_venta_btn = tk.Button(caja_frame, text="Nueva Venta",
                                   command=self.nueva_venta_directa,
                                   font=('Arial', 12, 'bold'),
                                   bg="#f39c12", fg="white", padx=30, pady=10)
        nueva_venta_btn.pack(pady=20)
    
    def create_admin_tab(self):
        """Crea la pestaña de administración"""
        admin_frame = ttk.Frame(self.notebook)
        self.notebook.add(admin_frame, text="Administración")
        
        tk.Label(admin_frame, text="PANEL DE ADMINISTRACIÓN", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Botones de administración
        buttons_frame = tk.Frame(admin_frame)
        buttons_frame.pack(pady=20)
        
        reportes_btn = tk.Button(buttons_frame, text="Ver Reportes",
                                font=('Arial', 12, 'bold'),
                                bg="#9b59b6", fg="white", padx=20, pady=10)
        reportes_btn.pack(pady=10, fill="x")
        
        productos_btn = tk.Button(buttons_frame, text="Gestionar Productos",
                                 font=('Arial', 12, 'bold'),
                                 bg="#1abc9c", fg="white", padx=20, pady=10)
        productos_btn.pack(pady=10, fill="x")
    
    def load_mesas(self):
        """Carga las mesas en el panel izquierdo"""
        # Limpiar mesas existentes
        for widget in self.mesas_frame.winfo_children():
            widget.destroy()
        
        try:
            mesas = self.db.get_mesas()
            
            # Crear botones de mesa en una grilla
            cols = 3
            for i, mesa in enumerate(mesas):
                row = i // cols
                col = i % cols
                
                mesa_id, numero, capacidad, estado = mesa
                
                # Color según estado
                color = {
                    'libre': '#2ecc71',
                    'ocupada': '#e74c3c',
                    'reservada': '#f39c12'
                }.get(estado, '#95a5a6')
                
                btn = tk.Button(self.mesas_frame, text=f"Mesa {numero}",
                               command=lambda m=mesa: self.seleccionar_mesa(m),
                               font=('Arial', 10, 'bold'),
                               bg=color, fg="white",
                               width=8, height=3)
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            
            # Configurar columnas para que se expandan uniformemente
            for i in range(cols):
                self.mesas_frame.grid_columnconfigure(i, weight=1)
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar mesas: {str(e)}")
    
    def seleccionar_mesa(self, mesa):
        """Selecciona una mesa para trabajar"""
        try:
            self.mesa_actual = mesa
            mesa_id, numero, capacidad, estado = mesa
            
            self.mesa_info_label.configure(text=f"Mesa {numero} - {estado.upper()}")
            
            # Buscar si hay pedido activo
            pedido_activo = self.db.get_pedido_activo_mesa(mesa_id)
            
            if pedido_activo:
                self.pedido_actual = pedido_activo[0]
            else:
                # Crear nuevo pedido si la mesa está libre
                if estado == 'libre':
                    self.pedido_actual = self.db.crear_pedido(mesa_id, self.usuario_actual[0])
                    self.load_mesas()  # Actualizar estado de mesas
            
            self.load_pedido_actual()
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al seleccionar mesa: {str(e)}")
    
    def load_productos(self):
        """Carga los productos según la categoría seleccionada"""
        # Limpiar productos existentes
        for widget in self.productos_frame.winfo_children():
            widget.destroy()
        
        try:
            categoria_id = self.categoria_var.get()
            categoria_id = None if categoria_id == "0" else int(categoria_id)
            
            productos = self.db.get_productos_por_categoria(categoria_id)
            
            # Crear frame con scroll
            canvas = tk.Canvas(self.productos_frame, bg="#ecf0f1")
            scrollbar = ttk.Scrollbar(self.productos_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#ecf0f1")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Crear botones de productos
            cols = 3
            for i, producto in enumerate(productos):
                row = i // cols
                col = i % cols
                
                prod_id, nombre, precio, stock, categoria = producto
                
                btn = tk.Button(scrollable_frame, 
                               text=f"{nombre}\n${precio:,.0f}",
                               command=lambda p=producto: self.agregar_producto(p),
                               font=('Arial', 9, 'bold'),
                               bg="#3498db", fg="white",
                               width=15, height=4,
                               wraplength=100)
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            
            # Configurar columnas
            for i in range(cols):
                scrollable_frame.grid_columnconfigure(i, weight=1)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar productos: {str(e)}")
    
    def agregar_producto(self, producto):
        """Agrega un producto al pedido actual"""
        if not self.pedido_actual:
            messagebox.showwarning("Advertencia", "Seleccione una mesa primero")
            return
        
        prod_id, nombre, precio, stock, categoria = producto
        
        # Ventana para seleccionar cantidad
        cantidad_window = tk.Toplevel(self.root)
        cantidad_window.title("Cantidad")
        cantidad_window.geometry("300x200")
        cantidad_window.configure(bg="#ecf0f1")
        cantidad_window.transient(self.root)
        cantidad_window.grab_set()
        
        # Centrar ventana
        cantidad_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        tk.Label(cantidad_window, text=f"Producto: {nombre}",
                font=('Arial', 12, 'bold'), bg="#ecf0f1").pack(pady=10)
        
        tk.Label(cantidad_window, text=f"Precio: ${precio:,.0f}",
                font=('Arial', 11), bg="#ecf0f1").pack(pady=5)
        
        tk.Label(cantidad_window, text="Cantidad:",
                font=('Arial', 11), bg="#ecf0f1").pack(pady=5)
        
        cantidad_var = tk.StringVar(value="1")
        cantidad_entry = tk.Entry(cantidad_window, textvariable=cantidad_var,
                                 font=('Arial', 14), width=10, justify="center")
        cantidad_entry.pack(pady=10)
        cantidad_entry.select_range(0, tk.END)
        cantidad_entry.focus()
        
        def confirmar():
            try:
                cantidad = int(cantidad_var.get())
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a cero")
                
                self.db.agregar_producto_pedido(self.pedido_actual, prod_id, cantidad)
                self.load_pedido_actual()
                cantidad_window.destroy()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Cantidad inválida: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar producto: {str(e)}")
        
        def cancelar():
            cantidad_window.destroy()
        
        buttons_frame = tk.Frame(cantidad_window, bg="#ecf0f1")
        buttons_frame.pack(pady=20)
        
        tk.Button(buttons_frame, text="Confirmar", command=confirmar,
                 font=('Arial', 11, 'bold'), bg="#27ae60", fg="white",
                 padx=20).pack(side="left", padx=10)
        
        tk.Button(buttons_frame, text="Cancelar", command=cancelar,
                 font=('Arial', 11), bg="#95a5a6", fg="white",
                 padx=20).pack(side="right", padx=10)
        
        # Bind Enter key
        cantidad_window.bind('<Return>', lambda e: confirmar())
        cantidad_window.bind('<Escape>', lambda e: cancelar())
    
    def load_pedido_actual(self):
        """Carga los detalles del pedido actual"""
        # Limpiar lista actual
        for widget in self.pedido_listbox_frame.winfo_children():
            widget.destroy()
        
        if not self.pedido_actual:
            self.total_label.configure(text="Total: $0.00")
            self.finalizar_btn.configure(state="disabled")
            self.cancelar_btn.configure(state="disabled")
            return
        
        try:
            detalles = self.db.get_detalles_pedido(self.pedido_actual)
            
            if not detalles:
                self.total_label.configure(text="Total: $0.00")
                self.finalizar_btn.configure(state="disabled")
                self.cancelar_btn.configure(state="disabled")
                return
            
            # Crear lista con scroll
            canvas = tk.Canvas(self.pedido_listbox_frame, bg="white")
            scrollbar = ttk.Scrollbar(self.pedido_listbox_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="white")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            total = 0
            for detalle in detalles:
                detalle_id, nombre, cantidad, precio_unit, subtotal = detalle
                total += subtotal
                
                # Frame para cada item
                item_frame = tk.Frame(scrollable_frame, bg="white", relief="solid", bd=1)
                item_frame.pack(fill="x", padx=2, pady=1)
                
                # Información del producto
                info_frame = tk.Frame(item_frame, bg="white")
                info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                
                tk.Label(info_frame, text=nombre, font=('Arial', 10, 'bold'),
                        bg="white", anchor="w").pack(fill="x")
                
                tk.Label(info_frame, text=f"{cantidad} x ${precio_unit:,.0f} = ${subtotal:,.0f}",
                        font=('Arial', 9), bg="white", fg="#666", anchor="w").pack(fill="x")
                
                # Botón eliminar
                del_btn = tk.Button(item_frame, text="✕", 
                                   command=lambda d_id=detalle_id: self.eliminar_detalle(d_id),
                                   font=('Arial', 8, 'bold'), bg="#e74c3c", fg="white",
                                   width=3)
                del_btn.pack(side="right", padx=5, pady=5)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Actualizar total
            self.total_label.configure(text=f"Total: ${total:,.0f}")
            self.finalizar_btn.configure(state="normal" if detalles else "disabled")
            self.cancelar_btn.configure(state="normal" if detalles else "disabled")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar pedido: {str(e)}")
    
    def eliminar_detalle(self, detalle_id):
        """Elimina un detalle del pedido"""
        if messagebox.askyesno("Confirmar", "¿Eliminar este producto del pedido?"):
            try:
                self.db.eliminar_detalle_pedido(detalle_id)
                self.load_pedido_actual()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar producto: {str(e)}")
    
    def cancelar_pedido_actual(self):
        """Cancela el pedido actual"""
        if not self.pedido_actual:
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de cancelar el pedido actual?\nEsto liberará la mesa y eliminará todos los productos."):
            try:
                self.db.cancelar_pedido(self.pedido_actual)
                
                # Limpiar pedido actual
                self.pedido_actual = None
                self.mesa_actual = None
                
                # Actualizar interfaz
                self.load_mesas()
                self.load_pedido_actual()
                self.mesa_info_label.configure(text="Seleccione una mesa")
                
                messagebox.showinfo("Éxito", "Pedido cancelado correctamente")
            
            except Exception as e:
                messagebox.showerror("Error", f"Error al cancelar pedido: {str(e)}")
    
    def generar_factura_pdf(self, pedido_id):
        """Genera una factura en PDF del pedido"""
        try:
            pedido_completo = self.db.get_pedido_completo(pedido_id)
            if not pedido_completo:
                messagebox.showerror("Error", "No se pudo obtener la información del pedido")
                return
            
            # Crear directorio de facturas si no existe
            if not os.path.exists("facturas"):
                os.makedirs("facturas")
            
            pedido_info = pedido_completo['pedido']
            filename = f"facturas/factura_{pedido_info[0]:06d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Crear documento PDF
            doc = SimpleDocTemplate(filename, pagesize=letter)
            story = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=20,
                alignment=TA_CENTER
            )
            
            normal_style = styles['Normal']
            
            # Encabezado
            story.append(Paragraph("FACTURA", title_style))
            story.append(Paragraph("Bar & Restaurant", header_style))
            story.append(Paragraph("Dirección: Calle Principal 123<br/>Tel: (341) 123-4567", header_style))
            story.append(Spacer(1, 20))
            
            # Información del pedido
            fecha_formateada = datetime.strptime(pedido_info[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
            
            info_data = [
                ['Factura N°:', f"{pedido_info[0]:06d}", 'Fecha:', fecha_formateada],
                ['Atendido por:', pedido_info[6], 'Método de Pago:', pedido_info[3].title()],
                ['Mesa N°:' if pedido_info[5] else 'Tipo:', 
                 pedido_info[5] if pedido_info[5] else 'Venta Directa', '', '']
            ]
            
            info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
            # Tabla de productos
            productos_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
            
            total_general = 0
            for detalle in pedido_completo['detalles']:
                cantidad, precio_unitario, subtotal, nombre = detalle
                total_general += subtotal
                productos_data.append([
                    nombre,
                    str(cantidad),
                    f"${precio_unitario:,.0f}",
                    f"${subtotal:,.0f}"
                ])
            
            # Agregar línea de total
            productos_data.append(['', '', 'TOTAL:', f"${total_general:,.0f}"])
            
            productos_table = Table(productos_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
            productos_table.setStyle(TableStyle([
                # Encabezados
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Contenido
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('ALIGN', (1, 1), (-1, -2), 'CENTER'),
                ('ALIGN', (0, 1), (0, -2), 'LEFT'),
                
                # Línea de total
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('ALIGN', (2, -1), (-1, -1), 'RIGHT'),
                ('BACKGROUND', (2, -1), (-1, -1), colors.lightgrey),
                
                # Bordes
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(productos_table)
            story.append(Spacer(1, 30))
            
            # Pie de página
            story.append(Paragraph("¡Gracias por su visita!", header_style))
            
            # Generar PDF
            doc.build(story)
            
            messagebox.showinfo("Éxito", f"Factura PDF generada: {filename}")
            
            # Abrir el PDF automáticamente (opcional)
            try:
                import subprocess
                import sys
                if sys.platform.startswith('win'):
                    os.startfile(filename)
                elif sys.platform.startswith('darwin'):
                    subprocess.call(['open', filename])
                else:
                    subprocess.call(['xdg-open', filename])
            except:
                pass  # Si no puede abrir automáticamente, no importa
                
        except ImportError:
            messagebox.showerror("Error", 
                               "ReportLab no está instalado.\n" + 
                               "Instale con: pip install reportlab")
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar factura PDF: {str(e)}")
    
    def finalizar_pedido(self):
        """Finaliza el pedido actual"""
        if not self.pedido_actual:
            return
        
        try:
            # Verificar que hay productos en el pedido
            detalles = self.db.get_detalles_pedido(self.pedido_actual)
            if not detalles:
                messagebox.showwarning("Advertencia", "No hay productos en el pedido")
                return
            
            # Ventana para seleccionar método de pago
            pago_window = tk.Toplevel(self.root)
            pago_window.title("Finalizar Pedido")
            pago_window.geometry("450x350")
            pago_window.configure(bg="#ecf0f1")
            pago_window.transient(self.root)
            pago_window.grab_set()
            
            # Centrar ventana
            pago_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
            
            tk.Label(pago_window, text="FINALIZAR PEDIDO", 
                    font=('Arial', 16, 'bold'), bg="#ecf0f1").pack(pady=20)
            
            # Mostrar total
            total = sum(d[4] for d in detalles)
            
            tk.Label(pago_window, text=f"Total a pagar: ${total:,.0f}",
                    font=('Arial', 14, 'bold'), bg="#ecf0f1", fg="#e74c3c").pack(pady=10)
            
            tk.Label(pago_window, text="Seleccionar método de pago:",
                    font=('Arial', 12), bg="#ecf0f1").pack(pady=10)
            
            # Métodos de pago
            pago_var = tk.StringVar(value="efectivo")
            
            metodos = [
                ("efectivo", "Efectivo"),
                ("tarjeta", "Tarjeta de Crédito/Débito"),
                ("transferencia", "Transferencia")
            ]
            
            for valor, texto in metodos:
                tk.Radiobutton(pago_window, text=texto, variable=pago_var, value=valor,
                              font=('Arial', 11), bg="#ecf0f1").pack(pady=5)
            
            def confirmar_pago():
                try:
                    metodo = pago_var.get()
                    pedido_finalizado = self.pedido_actual  # Guardar referencia antes de limpiar
                    
                    self.db.finalizar_pedido(self.pedido_actual, metodo)
                    
                    # Limpiar pedido actual
                    self.pedido_actual = None
                    self.mesa_actual = None
                    
                    # Actualizar interfaz
                    self.load_mesas()
                    self.load_pedido_actual()
                    self.mesa_info_label.configure(text="Seleccione una mesa")
                    
                    pago_window.destroy()
                    
                    # Generar factura PDF automáticamente
                    self.generar_factura_pdf(pedido_finalizado)
                    
                    messagebox.showinfo("Éxito", 
                                       f"Pedido finalizado correctamente\n"
                                       f"Total: ${total:,.0f}\n"
                                       f"Pago: {metodo.title()}\n"
                                       f"Factura generada automáticamente")
                
                except Exception as e:
                    messagebox.showerror("Error", f"Error al finalizar pedido: {str(e)}")
            
            def cancelar_pago():
                pago_window.destroy()
            
            buttons_frame = tk.Frame(pago_window, bg="#ecf0f1")
            buttons_frame.pack(pady=30)
            
            tk.Button(buttons_frame, text="Confirmar Pago", command=confirmar_pago,
                     font=('Arial', 12, 'bold'), bg="#27ae60", fg="white",
                     padx=30, pady=10).pack(side="left", padx=20)
            
            tk.Button(buttons_frame, text="Cancelar", command=cancelar_pago,
                     font=('Arial', 12), bg="#95a5a6", fg="white",
                     padx=30, pady=10).pack(side="right", padx=20)
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar finalización: {str(e)}")
    
    def nueva_venta_directa(self):
        """Crea una nueva venta directa en caja"""
        # Si ya hay una ventana abierta, enfocarla en lugar de crear una nueva
        if self.venta_directa_window and self.venta_directa_window.winfo_exists():
            self.venta_directa_window.lift()
            self.venta_directa_window.focus_force()
            return
            
        try:
            # Crear pedido sin mesa
            pedido_id = self.db.crear_pedido(None, self.usuario_actual[0], "caja")
            
            # Abrir ventana de venta directa
            self.abrir_ventana_venta_directa(pedido_id)
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear venta directa: {str(e)}")
    
    def abrir_ventana_venta_directa(self, pedido_id):
        """Abre la ventana de venta directa (ventana fija)"""
        self.venta_directa_window = tk.Toplevel(self.root)
        self.venta_directa_window.title("Venta Directa")
        self.venta_directa_window.geometry("900x700")
        self.venta_directa_window.configure(bg="#ecf0f1")
        
        # Hacer que la ventana sea modal y se mantenga siempre encima
        self.venta_directa_window.transient(self.root)
        self.venta_directa_window.grab_set()
        
        # Centrar la ventana
        self.venta_directa_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50, 
            self.root.winfo_rooty() + 50
        ))
        
        # Hacer que la ventana no se pueda cerrar con la X normal
        self.venta_directa_window.protocol("WM_DELETE_WINDOW", 
            lambda: self.confirmar_cierre_venta_directa(pedido_id))
        
        # Frame superior
        top_frame = tk.Frame(self.venta_directa_window, bg="#34495e", height=50)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        
        tk.Label(top_frame, text="VENTA DIRECTA EN CAJA",
                font=('Arial', 16, 'bold'), bg="#34495e", fg="white").pack(expand=True)
        
        # Frame principal
        main_frame = tk.Frame(self.venta_directa_window, bg="#ecf0f1")
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Panel izquierdo - Productos
        left_frame = tk.Frame(main_frame, bg="#ecf0f1")
        left_frame.pack(side="left", expand=True, fill="both")
        
        # Categorías para venta directa
        cat_frame = tk.Frame(left_frame, bg="#ecf0f1", height=50)
        cat_frame.pack(fill="x", pady=(0,10))
        cat_frame.pack_propagate(False)
        
        tk.Label(cat_frame, text="Categorías:", font=('Arial', 11, 'bold'),
                bg="#ecf0f1").pack(side="left", padx=5)
        
        categoria_directa_var = tk.StringVar()
        categorias = [("0", "Todas")] + self.db.get_categorias()
        
        for cat_id, cat_nombre in categorias:
            btn = tk.Radiobutton(cat_frame, text=cat_nombre,
                               variable=categoria_directa_var, value=cat_id,
                               command=lambda: self.load_productos_directa(productos_directa_frame, categoria_directa_var, pedido_id, actualizar_pedido_directa),
                               bg="#ecf0f1", font=('Arial', 10))
            btn.pack(side="left", padx=5)
        
        categoria_directa_var.set("0")
        
        # Frame de productos
        productos_directa_frame = tk.Frame(left_frame, bg="#ecf0f1")
        productos_directa_frame.pack(expand=True, fill="both")
        
        # Panel derecho - Pedido
        right_frame = tk.Frame(main_frame, bg="#ecf0f1", width=350)
        right_frame.pack(side="right", fill="y", padx=(10,0))
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="PRODUCTOS", font=('Arial', 12, 'bold'),
                bg="#ecf0f1").pack(pady=10)
        
        # Lista del pedido directo
        pedido_directa_frame = tk.Frame(right_frame, bg="#ecf0f1")
        pedido_directa_frame.pack(expand=True, fill="both", padx=10)
        
        # Total y botones
        total_directa_frame = tk.Frame(right_frame, bg="#ecf0f1", height=150)
        total_directa_frame.pack(fill="x", padx=10, pady=10)
        total_directa_frame.pack_propagate(False)
        
        total_directa_label = tk.Label(total_directa_frame, text="Total: $0.00",
                                     font=('Arial', 14, 'bold'), bg="#ecf0f1")
        total_directa_label.pack()
        
        finalizar_directa_btn = tk.Button(total_directa_frame, text="Finalizar Venta",
                                        command=lambda: self.finalizar_venta_directa(pedido_id, total_directa_label),
                                        font=('Arial', 11, 'bold'),
                                        bg="#27ae60", fg="white", state="disabled")
        finalizar_directa_btn.pack(pady=5, fill="x")
        
        cancelar_directa_btn = tk.Button(total_directa_frame, text="Cancelar Venta",
                                       command=lambda: self.cancelar_venta_directa(pedido_id),
                                       font=('Arial', 11), bg="#e74c3c", fg="white")
        cancelar_directa_btn.pack(fill="x")
        
        # Funciones auxiliares para la venta directa
        def actualizar_pedido_directa():
            # Limpiar lista actual
            for widget in pedido_directa_frame.winfo_children():
                widget.destroy()
            
            try:
                detalles = self.db.get_detalles_pedido(pedido_id)
                
                if not detalles:
                    total_directa_label.configure(text="Total: $0.00")
                    finalizar_directa_btn.configure(state="disabled")
                    return
                
                # Crear lista con scroll
                canvas = tk.Canvas(pedido_directa_frame, bg="white")
                scrollbar = ttk.Scrollbar(pedido_directa_frame, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas, bg="white")
                
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
                
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                total = 0
                for detalle in detalles:
                    detalle_id, nombre, cantidad, precio_unit, subtotal = detalle
                    total += subtotal
                    
                    # Frame para cada item
                    item_frame = tk.Frame(scrollable_frame, bg="white", relief="solid", bd=1)
                    item_frame.pack(fill="x", padx=2, pady=1)
                    
                    # Información del producto
                    info_frame = tk.Frame(item_frame, bg="white")
                    info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                    
                    tk.Label(info_frame, text=nombre, font=('Arial', 10, 'bold'),
                            bg="white", anchor="w").pack(fill="x")
                    
                    tk.Label(info_frame, text=f"{cantidad} x ${precio_unit:,.0f} = ${subtotal:,.0f}",
                            font=('Arial', 9), bg="white", fg="#666", anchor="w").pack(fill="x")
                    
                    # Botón eliminar
                    del_btn = tk.Button(item_frame, text="✕", 
                                       command=lambda d_id=detalle_id: eliminar_detalle_directa(d_id),
                                       font=('Arial', 8, 'bold'), bg="#e74c3c", fg="white",
                                       width=3)
                    del_btn.pack(side="right", padx=5, pady=5)
                
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
                # Actualizar total
                total_directa_label.configure(text=f"Total: ${total:,.0f}")
                finalizar_directa_btn.configure(state="normal" if detalles else "disabled")
            
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar pedido: {str(e)}")
        
        def eliminar_detalle_directa(detalle_id):
            if messagebox.askyesno("Confirmar", "¿Eliminar este producto?"):
                try:
                    self.db.eliminar_detalle_pedido(detalle_id)
                    actualizar_pedido_directa()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar producto: {str(e)}")
        
        # Cargar productos iniciales
        self.load_productos_directa(productos_directa_frame, categoria_directa_var, pedido_id, actualizar_pedido_directa)
        actualizar_pedido_directa()
    
    def confirmar_cierre_venta_directa(self, pedido_id):
        """Confirma si se debe cerrar la ventana de venta directa"""
        try:
            # Verificar si hay productos en el pedido
            detalles = self.db.get_detalles_pedido(pedido_id)
            
            if detalles:
                respuesta = messagebox.askyesnocancel(
                    "Cerrar Venta Directa",
                    "Hay productos en el pedido.\n\n"
                    "¿Desea finalizar la venta antes de cerrar?\n\n"
                    "• Sí: Finalizar venta\n"
                    "• No: Cancelar venta (se perderán los productos)\n"
                    "• Cancelar: Continuar editando"
                )
                
                if respuesta is True:  # Finalizar venta
                    # Intentar finalizar la venta
                    self.finalizar_venta_directa(pedido_id, None, cerrar_ventana=True)
                elif respuesta is False:  # Cancelar venta
                    self.cancelar_venta_directa(pedido_id, confirmar=False)
                # Si respuesta es None (Cancelar), no hacer nada
            else:
                # No hay productos, cancelar directamente
                self.cancelar_venta_directa(pedido_id, confirmar=False)
        except Exception as e:
            messagebox.showerror("Error", f"Error al cerrar ventana: {str(e)}")
    
    def load_productos_directa(self, productos_frame, categoria_var, pedido_id, callback=None):
        """Carga productos para venta directa"""
        # Limpiar productos existentes
        for widget in productos_frame.winfo_children():
            widget.destroy()
        
        try:
            categoria_id = categoria_var.get()
            categoria_id = None if categoria_id == "0" else int(categoria_id)
            
            productos = self.db.get_productos_por_categoria(categoria_id)
            
            # Crear frame con scroll
            canvas = tk.Canvas(productos_frame, bg="#ecf0f1")
            scrollbar = ttk.Scrollbar(productos_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#ecf0f1")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Crear botones de productos
            cols = 3
            for i, producto in enumerate(productos):
                row = i // cols
                col = i % cols
                
                prod_id, nombre, precio, stock, categoria = producto
                
                btn = tk.Button(scrollable_frame, 
                               text=f"{nombre}\n${precio:,.0f}",
                               command=lambda p=producto: self.agregar_producto_directa(p, pedido_id, callback),
                               font=('Arial', 9, 'bold'),
                               bg="#3498db", fg="white",
                               width=15, height=4,
                               wraplength=100)
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            
            # Configurar columnas
            for i in range(cols):
                scrollable_frame.grid_columnconfigure(i, weight=1)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar productos: {str(e)}")
    
    def agregar_producto_directa(self, producto, pedido_id, callback):
        """Agrega producto a venta directa"""
        prod_id, nombre, precio, stock, categoria = producto
        
        # Ventana para seleccionar cantidad
        cantidad_window = tk.Toplevel(self.venta_directa_window)
        cantidad_window.title("Cantidad")
        cantidad_window.geometry("300x200")
        cantidad_window.configure(bg="#ecf0f1")
        cantidad_window.transient(self.venta_directa_window)
        cantidad_window.grab_set()
        
        # Centrar ventana
        cantidad_window.geometry("+%d+%d" % (
            self.venta_directa_window.winfo_rootx() + 100, 
            self.venta_directa_window.winfo_rooty() + 100
        ))
        
        tk.Label(cantidad_window, text=f"Producto: {nombre}",
                font=('Arial', 12, 'bold'), bg="#ecf0f1").pack(pady=10)
        
        tk.Label(cantidad_window, text=f"Precio: ${precio:,.0f}",
                font=('Arial', 11), bg="#ecf0f1").pack(pady=5)
        
        tk.Label(cantidad_window, text="Cantidad:",
                font=('Arial', 11), bg="#ecf0f1").pack(pady=5)
        
        cantidad_var = tk.StringVar(value="1")
        cantidad_entry = tk.Entry(cantidad_window, textvariable=cantidad_var,
                                 font=('Arial', 14), width=10, justify="center")
        cantidad_entry.pack(pady=10)
        cantidad_entry.select_range(0, tk.END)
        cantidad_entry.focus()
        
        def confirmar():
            try:
                cantidad = int(cantidad_var.get())
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a cero")
                
                self.db.agregar_producto_pedido(pedido_id, prod_id, cantidad)
                if callback:
                    callback()
                cantidad_window.destroy()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Cantidad inválida: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar producto: {str(e)}")
        
        def cancelar():
            cantidad_window.destroy()
        
        buttons_frame = tk.Frame(cantidad_window, bg="#ecf0f1")
        buttons_frame.pack(pady=20)
        
        tk.Button(buttons_frame, text="Confirmar", command=confirmar,
                 font=('Arial', 11, 'bold'), bg="#27ae60", fg="white",
                 padx=20).pack(side="left", padx=10)
        
        tk.Button(buttons_frame, text="Cancelar", command=cancelar,
                 font=('Arial', 11), bg="#95a5a6", fg="white",
                 padx=20).pack(side="right", padx=10)
        
        cantidad_window.bind('<Return>', lambda e: confirmar())
        cantidad_window.bind('<Escape>', lambda e: cancelar())
    
    def cancelar_venta_directa(self, pedido_id, confirmar=True):
        """Cancela la venta directa"""
        if confirmar:
            if not messagebox.askyesno("Confirmar", "¿Está seguro de cancelar esta venta?\nSe perderán todos los productos agregados."):
                return
        
        try:
            self.db.cancelar_pedido(pedido_id)
            if self.venta_directa_window:
                self.venta_directa_window.destroy()
                self.venta_directa_window = None
            if confirmar:
                messagebox.showinfo("Cancelado", "Venta cancelada correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cancelar venta: {str(e)}")
    
    def finalizar_venta_directa(self, pedido_id, total_label, cerrar_ventana=False):
        """Finaliza la venta directa"""
        try:
            detalles = self.db.get_detalles_pedido(pedido_id)
            if not detalles:
                messagebox.showwarning("Advertencia", "No hay productos en la venta")
                return
            
            total = sum(d[4] for d in detalles)
            
            # Ventana para método de pago
            pago_window = tk.Toplevel(self.venta_directa_window)
            pago_window.title("Finalizar Venta")
            pago_window.geometry("450x350")
            pago_window.configure(bg="#ecf0f1")
            pago_window.transient(self.venta_directa_window)
            pago_window.grab_set()
            
            # Centrar ventana
            pago_window.geometry("+%d+%d" % (
                self.venta_directa_window.winfo_rootx() + 50, 
                self.venta_directa_window.winfo_rooty() + 50
            ))
            
            tk.Label(pago_window, text="FINALIZAR VENTA", 
                    font=('Arial', 16, 'bold'), bg="#ecf0f1").pack(pady=20)
            
            tk.Label(pago_window, text=f"Total: ${total:,.0f}",
                    font=('Arial', 14, 'bold'), bg="#ecf0f1", fg="#e74c3c").pack(pady=10)
            
            tk.Label(pago_window, text="Método de pago:",
                    font=('Arial', 12), bg="#ecf0f1").pack(pady=10)
            
            pago_var = tk.StringVar(value="efectivo")
            
            metodos = [
                ("efectivo", "Efectivo"),
                ("tarjeta", "Tarjeta de Crédito/Débito"),
                ("transferencia", "Transferencia")
            ]
            
            for valor, texto in metodos:
                tk.Radiobutton(pago_window, text=texto, variable=pago_var, value=valor,
                              font=('Arial', 11), bg="#ecf0f1").pack(pady=5)
            
            def confirmar_pago():
                try:
                    metodo = pago_var.get()
                    self.db.finalizar_pedido(pedido_id, metodo)
                    
                    pago_window.destroy()
                    if self.venta_directa_window:
                        self.venta_directa_window.destroy()
                        self.venta_directa_window = None
                    
                    # Generar factura PDF automáticamente
                    self.generar_factura_pdf(pedido_id)
                    
                    messagebox.showinfo("Éxito", 
                                       f"Venta finalizada correctamente\n"
                                       f"Total: ${total:,.0f}\n"
                                       f"Pago: {metodo.title()}\n"
                                       f"Factura generada automáticamente")
                
                except Exception as e:
                    messagebox.showerror("Error", f"Error al finalizar venta: {str(e)}")
            
            def cancelar_pago():
                pago_window.destroy()
            
            buttons_frame = tk.Frame(pago_window, bg="#ecf0f1")
            buttons_frame.pack(pady=30)
            
            tk.Button(buttons_frame, text="Confirmar", command=confirmar_pago,
                     font=('Arial', 12, 'bold'), bg="#27ae60", fg="white",
                     padx=30, pady=10).pack(side="left", padx=20)
            
            tk.Button(buttons_frame, text="Cancelar", command=cancelar_pago,
                     font=('Arial', 12), bg="#95a5a6", fg="white",
                     padx=30, pady=10).pack(side="right", padx=20)
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar venta: {str(e)}")
    
    def logout(self):
        """Cierra sesión del usuario"""
        if self.pedido_actual:
            if messagebox.askyesno("Confirmar", "Hay un pedido abierto. ¿Está seguro de cerrar sesión?"):
                self.usuario_actual = None
                self.pedido_actual = None
                self.mesa_actual = None
                # Cerrar ventana de venta directa si está abierta
                if self.venta_directa_window and self.venta_directa_window.winfo_exists():
                    self.venta_directa_window.destroy()
                    self.venta_directa_window = None
                self.create_login_screen()
        else:
            self.usuario_actual = None
            self.pedido_actual = None
            self.mesa_actual = None
            # Cerrar ventana de venta directa si está abierta
            if self.venta_directa_window and self.venta_directa_window.winfo_exists():
                self.venta_directa_window.destroy()
                self.venta_directa_window = None
            self.create_login_screen()
    
    def clear_screen(self):
        """Limpia la pantalla"""
        for widget in self.root.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    
    # Configurar para que se cierre correctamente
    def on_closing():
        if messagebox.askokcancel("Salir", "¿Está seguro de que desea salir del sistema?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        app = POSSystem(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error Fatal", f"Error al inicializar el sistema: {str(e)}")
        root.destroy()

if __name__ == "__main__":
    main()