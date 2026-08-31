# Importación de librerías necesarias para la interfaz gráfica (tkinter),
# manejo de mensajes/estilos y la conexión con la base de datos MySQL.
import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import random

# Configuración de los parámetros de conexión inicial hacia el servidor de base de datos MySQL.
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "101124",
    "database": "pos_system",
}

# Definición de la paleta de colores corporativa y moderna utilizada en toda la interfaz gráfica.
COLOR_BG_GRADIENT = "#4c1d95"
COLOR_BG_MAIN = "#f8fafc"
COLOR_CARD = "#ffffff"
COLOR_PRIMARY = "#7c3aed"
COLOR_PRIMARY_HOVER = "#6d28d9"
COLOR_TEXT_DARK = "#1e293b"
COLOR_TEXT_MUTED = "#64748b"


# Función auxiliar para calcular las dimensiones de la pantalla y centrar cualquier ventana emergente o principal.
def centrar_ventana(ventana, ancho, alto):
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = (pantalla_ancho - ancho) // 2
    y = (pantalla_alto - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


# Función global para gestionar y retornar la conexión activa a la base de datos, capturando errores si ocurren.
def conectar_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as err:
        messagebox.showerror(
            "Error de Conexión",
            f"No se pudo conectar a la base de datos:\n{err.msg}",
        )
        return None


# Clase que controla la ventana de autenticación (Login) mediante cédula y PIN de acceso.
class LoginWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("Cafetería - Restaurante | Iniciar Sesión")
        centrar_ventana(self.root, 460, 520)
        self.root.config(bg=COLOR_BG_GRADIENT)
        self.root.resizable(False, False)

        card_frame = tk.Frame(root, bg=COLOR_CARD, padx=40, pady=35)
        card_frame.place(relx=0.5, rely=0.5, anchor="center", width=390, height=450)

        tk.Label(
            card_frame,
            text="☕",
            font=("Segoe UI", 28),
            bg=COLOR_CARD,
            fg=COLOR_PRIMARY,
        ).pack()

        tk.Label(
            card_frame,
            text="Bienvenido",
            font=("Segoe UI", 18, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_DARK,
        ).pack(pady=(0, 2))

        tk.Label(
            card_frame,
            text="Ingrese sus credenciales para continuar",
            font=("Segoe UI", 9),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED,
        ).pack(pady=(0, 20))

        tk.Label(
            card_frame,
            text="CÉDULA",
            font=("Segoe UI", 8, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 3))

        self.entry_cedula = tk.Entry(
            card_frame,
            font=("Segoe UI", 11),
            bg="#f8fafc",
            fg=COLOR_TEXT_DARK,
            relief="solid",
            bd=1,
        )
        self.entry_cedula.pack(fill="x", ipady=6, pady=(0, 15))

        tk.Label(
            card_frame,
            text="PIN DE ACCESO",
            font=("Segoe UI", 8, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 3))

        self.entry_pin = tk.Entry(
            card_frame,
            font=("Segoe UI", 11),
            bg="#f8fafc",
            fg=COLOR_TEXT_DARK,
            show="•",
            relief="solid",
            bd=1,
        )
        self.entry_pin.pack(fill="x", ipady=6, pady=(0, 25))

        btn_ingresar = tk.Button(
            card_frame,
            text="INICIAR SESIÓN",
            command=self.verificar_login,
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground=COLOR_PRIMARY_HOVER,
            activeforeground="white",
        )
        btn_ingresar.pack(fill="x", ipady=8)

        self.root.bind("<Return>", lambda event: self.verificar_login())

    def verificar_login(self):
        cedula = self.entry_cedula.get().strip()
        pin = self.entry_pin.get().strip()

        if not cedula or not pin:
            messagebox.showwarning(
                "Campos Vacíos", "Por favor ingrese su cédula y su PIN."
            )
            return

        db = conectar_db()
        if not db:
            return
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM usuarios WHERE cedula = %s AND pin = %s", (cedula, pin)
        )
        usuario = cursor.fetchone()
        db.close()

        if usuario:
            self.root.destroy()
            main_root = tk.Tk()
            DashboardApp(main_root, usuario)
            main_root.mainloop()
        else:
            messagebox.showerror(
                "Error de Autenticación", "Cédula o PIN incorrectos."
            )


# Clase principal del sistema que despliega el panel con las pestañas de gestión.
class DashboardApp:

    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        
        # 🔄 Reiniciar todas las mesas a 'Libre' automáticamente al iniciar la aplicación principal
        self.reiniciar_mesas_a_libre()
        
        # Verificar y asegurar tablas de recetas e inventario en la base de datos
        self.verificar_tablas_recetas_inventario_db()

        # Verificar y asegurar la tabla de cierres de caja en la base de datos
        self.verificar_tabla_cierre_caja_db()

        # Diccionario para almacenar el estado de los pedidos de cada mesa o servicio de forma independiente
        self.pedidos_por_ubicacion = {}
        
        # Contador secuencial global para los números de orden de los pedidos
        self.contador_orden_secuencial = 1
        
        # Clave actual seleccionada por defecto (Ej: "Mesa #1")
        self.ubicacion_actual_key = "Mesa #1"

        # Variables de sesión para conectar la Caja con el Cierre de Caja
        self.fondo_inicial_caja = 0.0
        self.ventas_efectivo_sesion = 0.0
        self.ventas_totales_sesion = 0.0
        
        nombre_val = usuario.get('nombre', 'Usuario')
        rol_val = usuario.get('rol', 'General')

        self.root.title(
            f"Cafetería - Restaurante | Usuario: {nombre_val} ({rol_val})"
        )
        centrar_ventana(self.root, 1250, 700)
        self.root.config(bg=COLOR_BG_MAIN)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=COLOR_BG_MAIN, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            padding=[10, 5],
            font=("Segoe UI", 9, "bold"),
            background="#e2e8f0",
            foreground=COLOR_TEXT_MUTED,
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLOR_PRIMARY)],
            foreground=[("selected", "white")],
        )

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 45))
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        btn_logout = tk.Button(
            root,
            text="🚪 Cerrar Sesión",
            command=self.cerrar_sesion,
            bg="#ef4444",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5,
        )
        btn_logout.place(relx=0.98, rely=0.97, anchor="se")

        # Pestaña Apertura de Caja (Visible para Administrador y Cajero)
        self.tab_apertura = ttk.Frame(self.notebook)
        if rol_val in ["Administrador", "Cajero"]:
            self.notebook.add(self.tab_apertura, text="🔓 Apertura de Caja")
            self.init_apertura_tab()

        # Pestaña Pedidos (Visible para Administrador y Mesero)
        self.tab_pedidos = ttk.Frame(self.notebook)
        if rol_val in ["Administrador", "Mesero"]:
            self.notebook.add(self.tab_pedidos, text="📝 Pedidos")
            self.init_pedidos_tab()

        # Pestaña Salón (Visible para Administrador y Mesero)
        self.tab_salon = ttk.Frame(self.notebook)
        if rol_val in ["Administrador", "Mesero"]:
            self.notebook.add(self.tab_salon, text="🍽️ Salón")
            self.init_salon_tab()

        # Pestaña Cocina (Visible para Administrador y Cocinero)
        self.tab_cocina = ttk.Frame(self.notebook)
        if rol_val in ["Administrador", "Cocinero"]:
            self.notebook.add(self.tab_cocina, text="👨‍🍳 Cocina")
            self.init_cocina_tab()

        # Pestaña Caja / Cobro (Visible para Administrador y Cajero)
        self.tab_caja = ttk.Frame(self.notebook)
        if rol_val in ["Administrador", "Cajero"]:
            self.notebook.add(self.tab_caja, text="💵 Caja / Cobro")
            self.init_caja_tab()

        # Pestaña Cierre de Caja (Visible para Administrador y Cajero)
        self.tab_cierre = ttk.Frame(self.notebook)
        if rol_val in ["Administrador", "Cajero"]:
            self.notebook.add(self.tab_cierre, text="🔐 Cierre de Caja")
            self.init_cierre_tab()

        # Pestaña Inventario y Recetas (Visible para Administrador y Cocinero)
        self.tab_inventario = ttk.Frame(self.notebook)
        if rol_val in ["Administrador", "Cocinero"]:
            self.notebook.add(self.tab_inventario, text="📦 Inventario y Recetas")
            self.init_inventario_tab()

        self.tab_admin = ttk.Frame(self.notebook)
        if rol_val == "Administrador":
            self.notebook.add(self.tab_admin, text="👤 Administración")
            self.init_admin_tab()

    def verificar_tablas_recetas_inventario_db(self):
        """Verifica y crea las tablas necesarias en la BD para el inventario y las recetas de los platos."""
        db = conectar_db()
        if db:
            try:
                cursor = db.cursor()
                # Tabla de inventario de alimentos / ingredientes
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventario_alimentos (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        nombre VARCHAR(100) NOT NULL UNIQUE,
                        categoria VARCHAR(50) NOT NULL,
                        cantidad DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                        unidad VARCHAR(20) NOT NULL,
                        stock_min DECIMAL(10,2) NOT NULL DEFAULT 0.00
                    )
                """)
                # Tabla de relación de recetas (Plato -> Ingrediente y cantidad requerida)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recetas_platos (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        nombre_plato VARCHAR(100) NOT NULL,
                        ingrediente_id INT NOT NULL,
                        cantidad_requerida DECIMAL(10,2) NOT NULL DEFAULT 1.00,
                        FOREIGN KEY (ingrediente_id) REFERENCES inventario_alimentos(id) ON DELETE CASCADE
                    )
                """)
                db.commit()
            except Error as e:
                print(f"Error al verificar/crear tablas de inventario y recetas: {e}")
            finally:
                db.close()

    def verificar_tabla_cierre_caja_db(self):
        """Verifica y crea la tabla necesaria en la BD para registrar los cierres de caja."""
        db = conectar_db()
        if db:
            try:
                cursor = db.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cierres_caja (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        usuario_cedula VARCHAR(20) NOT NULL,
                        usuario_nombre VARCHAR(100) NOT NULL,
                        fecha_hora DATETIME NOT NULL,
                        total_contado DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                        fondo_inicial DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                        ventas_efectivo DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                        diferencia DECIMAL(10,2) NOT NULL DEFAULT 0.00
                    )
                """)
                db.commit()
            except Error as e:
                print(f"Error al verificar/crear tabla de cierres de caja: {e}")
            finally:
                db.close()

    def reiniciar_mesas_a_libre(self):
        """Restablece el estado de todas las mesas a 'Libre' al iniciar la aplicación."""
        db = conectar_db()
        if db:
            try:
                cursor = db.cursor()
                cursor.execute("UPDATE mesas SET estado = 'Libre'")
                db.commit()
            except Error as e:
                print(f"Error al restablecer el estado de las mesas: {e}")
            finally:
                db.close()

    def obtener_estado_actual(self):
        """Retorna el diccionario de pedido correspondiente a la mesa o servicio activo en pedidos."""
        tipo = self.tipo_servicio.get() if hasattr(self, "tipo_servicio") else "Mesa"
        if tipo == "Mesa":
            key = self.combo_mesa.get() if hasattr(self, "combo_mesa") else "Mesa #1"
        else:
            key = tipo

        if key not in self.pedidos_por_ubicacion:
            self.pedidos_por_ubicacion[key] = {
                "tipo_servicio": tipo,
                "ubicacion": key,
                "items": [],
                "nota": "",
                "total": 0.0,
                "saldo_pendiente": 0.0,
                "hora_llegada": None,
                "orden_numero": None
            }
        return self.pedidos_por_ubicacion[key]

    def on_tab_changed(self, event):
        try:
            if self.notebook.select() == str(self.tab_salon):
                self.cargar_mesas()
            elif hasattr(self, "tab_cocina") and self.notebook.select() == str(self.tab_cocina):
                self.actualizar_vista_cocina()
            elif self.notebook.select() == str(self.tab_caja):
                self.actualizar_combos_caja()
                self.actualizar_vista_caja()
            elif hasattr(self, "tab_cierre") and self.notebook.select() == str(self.tab_cierre):
                self.actualizar_resumen_cierre()
            elif hasattr(self, "tab_inventario") and self.notebook.select() == str(self.tab_inventario):
                self.cargar_tabla_inventario()
                self.actualizar_combo_recetas_platos()
                self.cargar_tabla_recetas()
        except Exception:
            pass

    def cerrar_sesion(self):
        """Verifica si existen saldos pendientes antes de permitir cerrar la sesión."""
        cuentas_pendientes = []
        for ubicacion, datos in self.pedidos_por_ubicacion.items():
            saldo = datos.get("saldo_pendiente", 0.0)
            if saldo > 0.0:
                cuentas_pendientes.append(f"• {ubicacion}: ${saldo:.2f}")

        if cuentas_pendientes:
            detalle_cuentas = "\n".join(cuentas_pendientes)
            messagebox.showerror(
                "Acción Denegada",
                f"No se puede cerrar sesión porque hay cuentas con saldo pendiente por cobrar:\n\n{detalle_cuentas}\n\nDebe cobrar o saldar todas las cuentas activas antes de salir."
            )
            return

        if messagebox.askyesno(
            "Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión actual?"
        ):
            self.root.destroy()
            login_root = tk.Tk()
            LoginWindow(login_root)
            login_root.mainloop()

    def init_salon_tab(self):
        salon_main = tk.Frame(self.tab_salon, bg=COLOR_BG_MAIN)
        salon_main.pack(fill="both", expand=True, padx=15, pady=15)

        header_salon = tk.Frame(salon_main, bg=COLOR_BG_MAIN)
        header_salon.pack(fill="x", pady=(0, 5))

        tk.Label(
            header_salon,
            text="Mapa Interactivo de Mesas",
            font=("Segoe UI", 14, "bold"),
            fg=COLOR_TEXT_DARK,
            bg=COLOR_BG_MAIN,
        ).pack(side="left")

        tk.Button(
            header_salon,
            text="🔄 Actualizar Mesas",
            command=self.cargar_mesas,
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(side="right")

        card_mesas = tk.Frame(
            salon_main,
            bg=COLOR_CARD,
            padx=15,
            pady=15,
            highlightbackground="#e2e8f0",
            highlightthickness=1,
        )
        card_mesas.pack(fill="both", expand=True)

        self.frame_mesas = tk.Frame(card_mesas, bg=COLOR_CARD)
        self.frame_mesas.pack(fill="both", expand=True)

        self.cargar_mesas()

    def cargar_mesas(self):
        for widget in self.frame_mesas.winfo_children():
            widget.destroy()

        db = conectar_db()
        if not db:
            return
        
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM mesas")
            res = cursor.fetchone()
            total_mesas = res["total"] if res else 0
            
            if total_mesas < 12:
                for i in range(total_mesas + 1, 13):
                    cursor.execute("INSERT INTO mesas (numero, estado) VALUES (%s, 'Libre')", (i,))
                db.commit()

            cursor.execute("SELECT * FROM mesas LIMIT 12")
            mesas = cursor.fetchall()
        except Error as e:
            messagebox.showerror("Error en Tabla Mesas", f"Detalle del error:\n{e}")
            mesas = []
        finally:
            db.close()

        colores = {
            "Libre": "#10b981",
            "Ocupada": "#ef4444",
            "Reservada": "#f59e0b",
            "Por limpiar": "#0ea5e9",
        }

        for index, mesa in enumerate(mesas):
            estado = mesa.get("estado", "Libre")
            color = colores.get(estado, "#cbd5e1")
            numero = mesa.get("numero", index + 1)
            
            txt_mesa = f"Mesa #{numero}\n• {estado} •"
            
            btn = tk.Button(
                self.frame_mesas,
                text=txt_mesa,
                bg=color,
                fg="white",
                width=20,
                height=4,
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                cursor="hand2",
                command=lambda m=mesa["id"], num=numero: self.cambiar_estado_mesa(m, num),
            )
            btn.grid(row=index // 4, column=index % 4, padx=12, pady=10)

    def cambiar_estado_mesa(self, mesa_id, numero_mesa):
        top = tk.Toplevel(self.root)
        top.title(f"Mesa {numero_mesa} - Gestión")
        centrar_ventana(top, 340, 340)
        top.config(bg=COLOR_CARD)
        top.resizable(False, False)

        tk.Label(
            top,
            text=f"Gestión Mesa #{numero_mesa}",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_DARK,
        ).pack(pady=10)

        frame_reserva = tk.Frame(top, bg=COLOR_CARD, padx=15)
        frame_reserva.pack(fill="x", pady=5)

        tk.Label(frame_reserva, text="Cliente (para Reservas):", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w")
        entry_cliente = tk.Entry(frame_reserva, font=("Segoe UI", 9), relief="solid", bd=1)
        entry_cliente.pack(fill="x", pady=(2, 6), ipady=2)

        tk.Label(frame_reserva, text="Hora (Ej: 20:30):", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w")
        entry_hora = tk.Entry(frame_reserva, font=("Segoe UI", 9), relief="solid", bd=1)
        entry_hora.pack(fill="x", pady=(2, 10), ipady=2)

        def actualizar(nuevo_estado):
            cliente = entry_cliente.get().strip()
            hora = entry_hora.get().strip()

            db = conectar_db()
            if db:
                cursor = db.cursor()
                cursor.execute(
                    "UPDATE mesas SET estado = %s WHERE id = %s",
                    (nuevo_estado, mesa_id),
                )
                db.commit()
                db.close()
                
                top.destroy()
                self.cargar_mesas()
                
                if nuevo_estado == "Reservada" and cliente:
                    messagebox.showinfo("Reserva Exitosa", f"Mesa {numero_mesa} reservada para {cliente} a las {hora}.")

        btn_frame = tk.Frame(top, bg=COLOR_CARD)
        btn_frame.pack(fill="x", padx=15, pady=5)

        tk.Button(btn_frame, text="🟢 Libre", bg="#10b981", fg="white", font=("Segoe UI", 8, "bold"), width=13, relief="flat", command=lambda: actualizar("Libre")).grid(row=0, column=0, padx=4, pady=3)
        tk.Button(btn_frame, text="🔴 Ocupada", bg="#ef4444", fg="white", font=("Segoe UI", 8, "bold"), width=13, relief="flat", command=lambda: actualizar("Ocupada")).grid(row=0, column=1, padx=4, pady=3)
        tk.Button(btn_frame, text="🟠 Reservada", bg="#f59e0b", fg="white", font=("Segoe UI", 8, "bold"), width=13, relief="flat", command=lambda: actualizar("Reservada")).grid(row=1, column=0, padx=4, pady=3)
        tk.Button(btn_frame, text="🔵 Por limpiar", bg="#0ea5e9", fg="white", font=("Segoe UI", 8, "bold"), width=13, relief="flat", command=lambda: actualizar("Por limpiar")).grid(row=1, column=1, padx=4, pady=3)

    def init_pedidos_tab(self):
        pedidos_main = tk.Frame(self.tab_pedidos, bg=COLOR_BG_MAIN)
        pedidos_main.pack(fill="both", expand=True, padx=15, pady=15)

        left_container = tk.Frame(pedidos_main, bg=COLOR_BG_MAIN)
        left_container.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            left_container,
            text="Gestión de Pedidos y Estaciones",
            font=("Segoe UI", 14, "bold"),
            fg=COLOR_TEXT_DARK,
            bg=COLOR_BG_MAIN,
        ).pack(anchor="w", pady=(0, 2))

        config_card = tk.Frame(left_container, bg=COLOR_CARD, padx=15, pady=12, highlightbackground="#e2e8f0", highlightthickness=1)
        config_card.pack(fill="x", pady=(0, 10))

        top_row = tk.Frame(config_card, bg=COLOR_CARD)
        top_row.pack(fill="x", pady=5)

        selectors_row = tk.Frame(top_row, bg=COLOR_CARD)
        selectors_row.pack(fill="x", pady=(0, 8))

        serv_frame = tk.Frame(selectors_row, bg=COLOR_CARD)
        serv_frame.pack(side="left", padx=(0, 15))
        tk.Label(serv_frame, text="TIPO DE SERVICIO", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w")
        self.tipo_servicio = ttk.Combobox(serv_frame, values=["Mesa", "Para llevar", "Delivery"], width=20, state="readonly")
        self.tipo_servicio.pack(anchor="w", pady=(2, 0))
        self.tipo_servicio.current(0)
        self.tipo_servicio.bind("<<ComboboxSelected>>", self.on_tipo_servicio_changed)

        self.mesa_frame = tk.Frame(selectors_row, bg=COLOR_CARD)
        self.mesa_frame.pack(side="left")
        tk.Label(self.mesa_frame, text="CÓDIGO / ORDEN DE MESA", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w")
        
        self.combo_mesa = ttk.Combobox(self.mesa_frame, values=["Mesa #1", "Mesa #2", "Mesa #3", "Mesa #4", "Mesa #5", "Mesa #6", "Mesa #7", "Mesa #8", "Mesa #9", "Mesa #10", "Mesa #11", "Mesa #12"], width=22, state="readonly")
        self.combo_mesa.pack(anchor="w", pady=(2, 0))
        self.combo_mesa.current(0)
        self.combo_mesa.bind("<<ComboboxSelected>>", self.on_mesa_seleccionada)

        tk.Label(top_row, text="NOTA / OBSERVACIONES", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w")
        self.text_nota_pedido = tk.Entry(top_row, font=("Segoe UI", 9), bg="#f8fafc", relief="solid", bd=1)
        self.text_nota_pedido.pack(fill="x", ipady=4, pady=(2, 0))
        self.text_nota_pedido.bind("<KeyRelease>", self.on_nota_changed)

        # Contenedor con scroll para el catálogo amplio de platillos y bebidas
        catalogo_container_outer = tk.Frame(left_container, bg=COLOR_BG_MAIN)
        catalogo_container_outer.pack(fill="both", expand=True)

        canvas_cat = tk.Canvas(catalogo_container_outer, bg=COLOR_BG_MAIN, highlightthickness=0)
        scrollbar_cat = ttk.Scrollbar(catalogo_container_outer, orient="vertical", command=canvas_cat.yview)
        
        catalogo_frame = tk.Frame(canvas_cat, bg=COLOR_BG_MAIN)
        catalogo_frame.bind(
            "<Configure>",
            lambda e: canvas_cat.configure(scrollregion=canvas_cat.bbox("all"))
        )

        canvas_cat.create_window((0, 0), window=catalogo_frame, anchor="nw")
        canvas_cat.configure(yscrollcommand=scrollbar_cat.set)

        canvas_cat.pack(side="left", fill="both", expand=True)
        scrollbar_cat.pack(side="right", fill="y")

        # Catálogo ampliado y categorizado para cafetería-restaurante
        platillos = [
            # --- CAFETERÍA Y BEBIDAS ---
            "Café Americano",
            "Capuchino",
            "Café Espresso",
            "Café Latte",
            "Mocaccino",
            "Chocolate Caliente",
            "Te Aromático / Infusión",
            "Jugo Natural de Fruta",
            "Limonada Natural",
            "Limonada Hatsu / Fresa",
            "Gaseosa Personal",
            "Agua Mineral",
            
            # --- DESAYUNOS Y PANADERÍA ---
            "Croissant Relleno",
            "Tostadas Francesas",
            "Panqueques con Miel",
            "Bolón de Queso / Chicharrón",
            "Tigrillo Lojano",
            "Desayuno Americano",
            
            # --- ENTRADAS Y PLATOS LIGEROS ---
            "Sandwich Club",
            "Hamburguesa Clásica",
            "Hamburguesa de la Casa",
            "Wrap de Pollo",
            "Salchipapa Tradicional",
            "Porción de Papas Fritas",
            
            # --- PLATOS FUERTES Y ESPECIALIDADES ---
            "Pasta Carbonara",
            "Lomo Fino a la Plancha",
            "Pechuga de Pollo Gratinada",
            "Seco de Pollo Tradicional",
            "Arroz con Pollo",
            
            # --- ENSALADAS ---
            "Ensalada César",
            "Ensalada Tropical de Pollo",
            
            # --- POSTRES Y DULCES ---
            "Tiramisú",
            "Cheesecake de Maracuyá",
            "Tres Leches",
            "Brownie con Helado",
            "Pie de Limón"
        ]

        self.precios_catalogo = {
            # Cafetería y Bebidas
            "Café Americano": 1.75,
            "Capuchino": 2.50,
            "Café Espresso": 1.50,
            "Café Latte": 2.25,
            "Mocaccino": 2.75,
            "Chocolate Caliente": 2.50,
            "Te Aromático / Infusión": 1.50,
            "Jugo Natural de Fruta": 2.25,
            "Limonada Natural": 2.00,
            "Limonada Hatsu / Fresa": 2.75,
            "Gaseosa Personal": 1.50,
            "Agua Mineral": 1.25,
            
            # Desayunos y Panadería
            "Croissant Relleno": 2.25,
            "Tostadas Francesas": 3.50,
            "Panqueques con Miel": 3.75,
            "Bolón de Queso / Chicharrón": 3.00,
            "Tigrillo Lojano": 4.50,
            "Desayuno Americano": 5.50,
            
            # Entradas y Platos Ligeros
            "Sandwich Club": 5.50,
            "Hamburguesa Clásica": 6.00,
            "Hamburguesa de la Casa": 7.25,
            "Wrap de Pollo": 5.00,
            "Salchipapa Tradicional": 4.00,
            "Porción de Papas Fritas": 2.50,
            
            # Platos Fuertes y Especialidades
            "Pasta Carbonara": 7.50,
            "Lomo Fino a la Plancha": 9.50,
            "Pechuga de Pollo Gratinada": 8.00,
            "Seco de Pollo Tradicional": 6.50,
            "Arroz con Pollo": 6.00,
            
            # Ensaladas
            "Ensalada César": 5.00,
            "Ensalada Tropical de Pollo": 6.25,
            
            # Postres y Dulces
            "Tiramisú": 3.75,
            "Cheesecake de Maracuyá": 3.50,
            "Tres Leches": 3.25,
            "Brownie con Helado": 3.50,
            "Pie de Limón": 3.00
        }

        for index, nombre in enumerate(platillos):
            r = index // 4
            c = index % 4

            card = tk.Frame(catalogo_frame, bg=COLOR_CARD, highlightbackground="#e2e8f0", highlightthickness=1, padx=8, pady=8, width=140, height=85)
            card.grid_propagate(False)
            card.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

            tk.Label(card, text=nombre, font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK, wraplength=125, justify="center").pack(anchor="n", pady=(2, 4))

            btn_add = tk.Button(
                card,
                text="+ Agregar",
                bg=COLOR_PRIMARY,
                fg="white",
                font=("Segoe UI", 8, "bold"),
                relief="flat",
                cursor="hand2",
                command=lambda n=nombre: self.agregar_al_carrito(n)
            )
            btn_add.pack(side="bottom", fill="x", ipady=2)

        right_panel = tk.Frame(pedidos_main, bg=COLOR_CARD, width=300, padx=15, pady=15, highlightbackground="#e2e8f0", highlightthickness=1)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        tk.Label(right_panel, text="Resumen del pedido", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(anchor="w")
        self.lbl_info_mesa = tk.Label(right_panel, text="Mesa #1 · 0 items", font=("Segoe UI", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
        self.lbl_info_mesa.pack(anchor="w", pady=(0, 15))

        self.frame_items_carrito = tk.Frame(right_panel, bg=COLOR_CARD)
        self.frame_items_carrito.pack(fill="both", expand=True)

        self.lbl_vacio = tk.Label(self.frame_items_carrito, text="🛒\n\nAgrega platillos al pedido", font=("Segoe UI", 9), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, justify="center")
        self.lbl_vacio.pack(pady=40)

        footer_carrito = tk.Frame(right_panel, bg=COLOR_CARD)
        footer_carrito.pack(fill="x", side="bottom")

        tot_row = tk.Frame(footer_carrito, bg=COLOR_CARD)
        tot_row.pack(fill="x", pady=(10, 10))
        tk.Label(tot_row, text="Total", font=("Segoe UI", 10, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(side="left")
        self.lbl_total = tk.Label(tot_row, text="$0.00", font=("Segoe UI", 12, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK)
        self.lbl_total.pack(side="right")

        tk.Button(
            footer_carrito,
            text="Enviar a Cocina",
            command=self.enviar_pedido,
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        ).pack(fill="x")

        self.actualizar_vista_carrito()

    def on_tipo_servicio_changed(self, event):
        tipo = self.tipo_servicio.get()
        if tipo == "Mesa":
            self.mesa_frame.pack(side="left")
        else:
            self.mesa_frame.pack_forget()
        self.actualizar_vista_carrito()

    def on_mesa_seleccionada(self, event):
        self.actualizar_vista_carrito()

    def on_nota_changed(self, event):
        estado = self.obtener_estado_actual()
        estado["nota"] = self.text_nota_pedido.get().strip()

    def agregar_al_carrito(self, nombre):
        estado = self.obtener_estado_actual()
        precio = self.precios_catalogo.get(nombre, 0.0)
        
        for item in estado["items"]:
            if item["nombre"] == nombre:
                item["cantidad"] += 1
                self.actualizar_vista_carrito()
                return
        
        estado["items"].append({"nombre": nombre, "precio": precio, "cantidad": 1})
        self.actualizar_vista_carrito()

    def actualizar_vista_carrito(self):
        for widget in self.frame_items_carrito.winfo_children():
            widget.destroy()

        estado = self.obtener_estado_actual()
        servicio_actual = self.tipo_servicio.get()
        estado["tipo_servicio"] = servicio_actual
        
        if servicio_actual == "Mesa":
            ubicacion_str = self.combo_mesa.get()
            estado["ubicacion"] = ubicacion_str
        else:
            ubicacion_str = servicio_actual
            estado["ubicacion"] = servicio_actual

        self.text_nota_pedido.delete(0, tk.END)
        self.text_nota_pedido.insert(0, estado.get("nota", ""))

        cargo_extra = 0.0
        nombre_extra = ""
        if servicio_actual == "Para llevar":
            cargo_extra = 0.50
            nombre_extra = "Cubiertos Desechables"
        elif servicio_actual == "Delivery":
            cargo_extra = 2.00
            nombre_extra = "Costo de Envío / Carrera"

        total_items_count = sum(item["cantidad"] for item in estado["items"])
        info_texto = f"{ubicacion_str} · {total_items_count} items"

        if not estado["items"] and cargo_extra == 0.0:
            self.lbl_vacio = tk.Label(self.frame_items_carrito, text="🛒\n\nAgrega platillos al pedido", font=("Segoe UI", 9), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, justify="center")
            self.lbl_vacio.pack(pady=40)
            self.lbl_total.config(text="$0.00")
            self.lbl_info_mesa.config(text=info_texto)
            estado["total"] = 0.0
            estado["saldo_pendiente"] = 0.0
            return

        self.lbl_info_mesa.config(text=info_texto)
        total = 0

        for idx, item in enumerate(estado["items"]):
            subtotal_item = item["precio"] * item["cantidad"]
            total += subtotal_item

            row_item = tk.Frame(self.frame_items_carrito, bg=COLOR_CARD)
            row_item.pack(fill="x", pady=2)

            texto_lbl = f"{item['nombre']} (x{item['cantidad']})" if item['cantidad'] > 1 else item['nombre']
            tk.Label(row_item, text=texto_lbl, font=("Segoe UI", 8), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(side="left")
            tk.Label(row_item, text=f"${subtotal_item:.2f}", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(side="right", padx=(5, 0))

            btn_del = tk.Button(row_item, text="✕", fg="#ef4444", bg=COLOR_CARD, font=("Segoe UI", 8), relief="flat", cursor="hand2", command=lambda i=idx: self.remover_item_carrito(i))
            btn_del.pack(side="right")

        if cargo_extra > 0.0:
            total += cargo_extra
            row_extra = tk.Frame(self.frame_items_carrito, bg=COLOR_CARD)
            row_extra.pack(fill="x", pady=2)

            tk.Label(row_extra, text=f"📦 {nombre_extra}", font=("Segoe UI", 8, "italic"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(side="left")
            tk.Label(row_extra, text=f"${cargo_extra:.2f}", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(side="right", padx=(5, 0))

        estado["total"] = total
        if estado.get("enviado_cocina", False):
            if estado["saldo_pendiente"] <= 0.0 or estado["saldo_pendiente"] > total:
                estado["saldo_pendiente"] = total
        else:
            estado["saldo_pendiente"] = 0.0
            
        self.lbl_total.config(text=f"${total:.2f}")

    def remover_item_carrito(self, index):
        estado = self.obtener_estado_actual()
        if estado["items"][index]["cantidad"] > 1:
            estado["items"][index]["cantidad"] -= 1
        else:
            estado["items"].pop(index)
        self.actualizar_vista_carrito()

    def enviar_pedido(self):
        estado = self.obtener_estado_actual()
        if not estado["items"]:
            messagebox.showwarning("Pedido Vacío", "Debe agregar al menos un platillo al pedido.")
            return

        estado["nota"] = self.text_nota_pedido.get().strip()
        estado["enviado_cocina"] = True
        
        total_cuenta = estado.get("total", 0.0)
        estado["saldo_pendiente"] = total_cuenta
        
        hora_actual = datetime.now().strftime("%H:%M:%S")
        estado["hora_llegada"] = hora_actual

        if not estado.get("orden_numero"):
            estado["orden_numero"] = self.contador_orden_secuencial
            self.contador_orden_secuencial += 1

        if estado["tipo_servicio"] == "Mesa":
            mesa_str = estado["ubicacion"]
            try:
                numero_mesa = int(mesa_str.split("#")[1])
                db = conectar_db()
                if db:
                    cursor = db.cursor()
                    cursor.execute("UPDATE mesas SET estado = 'Ocupada' WHERE numero = %s", (numero_mesa,))
                    db.commit()
                    db.close()
            except Exception as e:
                print(f"Error actualizando mesa a ocupada: {e}")

        mensaje_popup = (
            f"N° de Orden: #{estado['orden_numero']:03d}\n"
            f"Servicio: {estado['tipo_servicio']}\n"
            f"Ubicación: {estado['ubicacion']}\n"
            f"Hora de Llegada (Cola): {hora_actual}\n"
            f"Total calculado: ${total_cuenta:.2f}\n\n"
            f"¡Orden registrada y enviada a cocina!"
        )
        messagebox.showinfo("Pedido Enviado a Cocina", mensaje_popup)
        self.actualizar_vista_carrito()

    def init_cocina_tab(self):
        """Inicializa la interfaz de la pestaña de Cocina para ver platos, ingredientes y descontar inventario."""
        cocina_main = tk.Frame(self.tab_cocina, bg=COLOR_BG_MAIN)
        cocina_main.pack(fill="both", expand=True, padx=15, pady=15)

        header_cocina = tk.Frame(cocina_main, bg=COLOR_BG_MAIN)
        header_cocina.pack(fill="x", pady=(0, 10))

        tk.Label(
            header_cocina,
            text="👨‍🍳 Monitoreo de Pedidos, Ingredientes y Descuento Automático",
            font=("Segoe UI", 14, "bold"),
            fg=COLOR_TEXT_DARK,
            bg=COLOR_BG_MAIN,
        ).pack(side="left")

        tk.Button(
            header_cocina,
            text="🔄 Actualizar Órdenes",
            command=self.actualizar_vista_cocina,
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(side="right")

        # Contenedor con scroll para mostrar las tarjetas de órdenes activas de cocina
        cocina_container_outer = tk.Frame(cocina_main, bg=COLOR_BG_MAIN)
        cocina_container_outer.pack(fill="both", expand=True)

        self.canvas_cocina = tk.Canvas(cocina_container_outer, bg=COLOR_BG_MAIN, highlightthickness=0)
        scrollbar_cocina = ttk.Scrollbar(cocina_container_outer, orient="vertical", command=self.canvas_cocina.yview)
        
        self.frame_tarjetas_cocina = tk.Frame(self.canvas_cocina, bg=COLOR_BG_MAIN)
        self.frame_tarjetas_cocina.bind(
            "<Configure>",
            lambda e: self.canvas_cocina.configure(scrollregion=self.canvas_cocina.bbox("all"))
        )

        self.canvas_cocina.create_window((0, 0), window=self.frame_tarjetas_cocina, anchor="nw")
        self.canvas_cocina.configure(yscrollcommand=scrollbar_cocina.set)

        self.canvas_cocina.pack(side="left", fill="both", expand=True)
        scrollbar_cocina.pack(side="right", fill="y")

        self.actualizar_vista_cocina()

    def obtener_ingredientes_plato(self, nombre_plato):
        """Consulta en la base de datos los ingredientes y cantidades necesarios para un plato específico[cite: 6]."""
        db = conectar_db()
        ingredientes = []
        if db:
            try:
                cursor = db.cursor(dictionary=True)
                sql = """
                    SELECT i.nombre, r.cantidad_requerida, i.unidad 
                    FROM recetas_platos r 
                    JOIN inventario_alimentos i ON r.ingrediente_id = i.id 
                    WHERE r.nombre_plato = %s
                """
                cursor.execute(sql, (nombre_plato,))
                ingredientes = cursor.fetchall()
            except Error as e:
                print(f"Error al consultar ingredientes del plato {nombre_plato}: {e}")
            finally:
                db.close()
        return ingredientes

    def actualizar_vista_cocina(self):
        """Refresca y dibuja las tarjetas de pedidos enviados a cocina mostrando sus platos e ingredientes."""
        if not hasattr(self, "frame_tarjetas_cocina"):
            return

        for widget in self.frame_tarjetas_cocina.winfo_children():
            widget.destroy()

        # Filtrar solo aquellos que ya fueron enviados a cocina y tienen items activos
        pedidos_activos = [
            datos for datos in self.pedidos_por_ubicacion.values()
            if datos.get("enviado_cocina", False) and datos.get("items")
        ]

        if not pedidos_activos:
            tk.Label(
                self.frame_tarjetas_cocina,
                text="👨‍🍳\n\nNo hay pedidos activos en la cocina en este momento.",
                font=("Segoe UI", 11),
                bg=COLOR_BG_MAIN,
                fg=COLOR_TEXT_MUTED,
                justify="center"
            ).pack(pady=80, padx=200)
            return

        # Organizar las tarjetas de cocina en una cuadrícula de 3 columnas
        for index, pedido in enumerate(pedidos_activos):
            r = index // 3
            c = index % 3

            card = tk.Frame(
                self.frame_tarjetas_cocina,
                bg=COLOR_CARD,
                highlightbackground="#e2e8f0",
                highlightthickness=1,
                padx=10,
                pady=10,
                width=380,
                height=320
            )
            card.grid_propagate(False)
            card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")

            # Encabezado de la orden
            orden_num = pedido.get("orden_numero", 0)
            ubicacion = pedido.get("ubicacion", "Mesa")
            hora = pedido.get("hora_llegada", "--:--")

            header_card = tk.Frame(card, bg=COLOR_PRIMARY, padx=8, pady=6)
            header_card.pack(fill="x", pady=(0, 6))

            tk.Label(
                header_card,
                text=f"ORDEN #{orden_num:03d} — {ubicacion}",
                font=("Segoe UI", 10, "bold"),
                bg=COLOR_PRIMARY,
                fg="white"
            ).pack(side="left")

            tk.Label(
                header_card,
                text=f"🕒 {hora}",
                font=("Segoe UI", 8, "bold"),
                bg=COLOR_PRIMARY,
                fg="#f3e8ff"
            ).pack(side="right")

            # Detalle de Observaciones / Nota si existe
            nota = pedido.get("nota", "")
            if nota:
                lbl_nota = tk.Label(
                    card,
                    text=f"📝 Nota: {nota}",
                    font=("Segoe UI", 8, "italic"),
                    bg="#fef3c7",
                    fg="#92400e",
                    padx=5,
                    pady=2,
                    anchor="w"
                )
                lbl_nota.pack(fill="x", pady=(0, 4))

            # Contenedor con scroll interno para los platillos e ingredientes de la tarjeta
            canvas_card_inner = tk.Canvas(card, bg=COLOR_CARD, highlightthickness=0, height=180)
            scrollbar_card_inner = ttk.Scrollbar(card, orient="vertical", command=canvas_card_inner.yview)
            
            items_frame = tk.Frame(canvas_card_inner, bg=COLOR_CARD)
            items_frame.bind(
                "<Configure>",
                lambda e: canvas_card_inner.configure(scrollregion=canvas_card_inner.bbox("all"))
            )
            canvas_card_inner.create_window((0, 0), window=items_frame, anchor="nw")
            canvas_card_inner.configure(yscrollcommand=scrollbar_card_inner.set)

            canvas_card_inner.pack(side="top", fill="both", expand=True, pady=(0, 5))
            scrollbar_card_inner.pack(side="right", fill="y")

            for item in pedido.get("items", []):
                nombre_plato = item['nombre']
                cant_plato = item['cantidad']
                
                # Marco para cada plato
                f_plato = tk.Frame(items_frame, bg="#f8fafc", padx=6, pady=4, highlightbackground="#e2e8f0", highlightthickness=1)
                f_plato.pack(fill="x", pady=3)

                lbl_encabezado_plato = tk.Label(
                    f_plato, 
                    text=f"🍽️ {cant_plato}x {nombre_plato}", 
                    font=("Segoe UI", 9, "bold"), 
                    bg="#f8fafc", 
                    fg=COLOR_TEXT_DARK, 
                    anchor="w"
                )
                lbl_encabezado_plato.pack(fill="x")

                # Obtener e imprimir ingredientes asociados a este plato
                ingredientes = self.obtener_ingredientes_plato(nombre_plato)
                if ingredientes:
                    tk.Label(f_plato, text="Ingredientes necesarios[cite: 6]:", font=("Segoe UI", 7, "bold"), bg="#f8fafc", fg=COLOR_TEXT_MUTED, anchor="w").pack(fill="x")
                    for ing in ingredientes:
                        cant_necesaria = float(ing['cantidad_requerida']) * cant_plato
                        txt_ing = f"   • {ing['nombre']}: {cant_necesaria} {ing['unidad']}"
                        tk.Label(f_plato, text=txt_ing, font=("Segoe UI", 8), bg="#f8fafc", fg=COLOR_PRIMARY, anchor="w").pack(fill="x")
                else:
                    tk.Label(f_plato, text="   ⚠️ Sin ingredientes configurados en receta.", font=("Segoe UI", 7, "italic"), bg="#f8fafc", fg="#ef4444", anchor="w").pack(fill="x")

            # Botón para marcar la orden como lista, descontando automáticamente el inventario[cite: 6]
            btn_terminar = tk.Button(
                card,
                text="✅ Marcar Orden Lista y Descontar Inventario",
                command=lambda ub=ubicacion: self.completar_pedido_cocina(ub),
                bg="#10b981",
                fg="white",
                font=("Segoe UI", 8, "bold"),
                relief="flat",
                cursor="hand2",
                height=2
            )
            btn_terminar.pack(side="bottom", fill="x", pady=(2, 0))

    def completar_pedido_cocina(self, ubicacion_key):
        """Marca el pedido como completado en cocina, descuenta automáticamente los ingredientes del inventario y lo retira de la vista."""
        if ubicacion_key not in self.pedidos_por_ubicacion:
            return

        pedido = self.pedidos_por_ubicacion[ubicacion_key]
        items = pedido.get("items", [])

        if not items:
            pedido["enviado_cocina"] = False
            self.actualizar_vista_cocina()
            return

        db = conectar_db()
        if not db:
            return

        ingredientes_descontados = []
        platos_sin_receta = []

        try:
            cursor = db.cursor(dictionary=True)

            # Recorrer todos los ítems del pedido para descontar sus ingredientes
            for item in items:
                nombre_plato = item['nombre'].strip()
                cant_plato = item['cantidad']

                # Se consulta la receta usando la MISMA conexión/cursor para garantizar
                # que la lectura y el descuento del inventario sean consistentes.
                cursor.execute("""
                    SELECT i.id, i.nombre, r.cantidad_requerida, i.unidad
                    FROM recetas_platos r
                    JOIN inventario_alimentos i ON r.ingrediente_id = i.id
                    WHERE r.nombre_plato = %s
                """, (nombre_plato,))
                ingredientes = cursor.fetchall()

                if not ingredientes:
                    # El plato no tiene receta configurada: no hay nada que descontar
                    # para este ítem, se informa al finalizar en vez de fallar en silencio.
                    platos_sin_receta.append(nombre_plato)
                    continue

                for ing in ingredientes:
                    cant_a_descontar = round(float(ing['cantidad_requerida']) * cant_plato, 2)
                    # Se descuenta identificando el ingrediente por su ID (más confiable que por nombre)
                    cursor.execute(
                        "UPDATE inventario_alimentos SET cantidad = GREATEST(0.00, cantidad - %s) WHERE id = %s",
                        (cant_a_descontar, ing['id'])
                    )
                    ingredientes_descontados.append(f"{ing['nombre']}: -{cant_a_descontar:.2f} {ing['unidad']}")

            db.commit()

            resumen = ""
            if ingredientes_descontados:
                resumen += "Ingredientes descontados del inventario:\n" + "\n".join(f"• {d}" for d in ingredientes_descontados)
            if platos_sin_receta:
                resumen += (
                    "\n\n⚠️ Estos platos NO tienen receta configurada, por lo que no se descontó stock de ellos:\n"
                    + "\n".join(f"• {p}" for p in platos_sin_receta)
                    + "\n\nConfigúralos en la pestaña 'Inventario y Recetas' para que su stock se descuente automáticamente."
                )
            if not resumen:
                resumen = "No había ítems para descontar."

            messagebox.showinfo(
                "Inventario Actualizado",
                f"La orden de [{ubicacion_key}] ha sido despachada.\n\n{resumen}"
            )
        except Error as e:
            messagebox.showerror("Error de Base de Datos", f"No se pudo descontar el inventario automáticamente:\n{e}")
            db.close()
            return
        finally:
            db.close()

        pedido["enviado_cocina"] = False
        self.actualizar_vista_cocina()


    def init_inventario_tab(self):
        """Inicializa la interfaz de la pestaña de Inventario de Alimentos y parametrización de Recetas."""
        inv_main = tk.Frame(self.tab_inventario, bg=COLOR_BG_MAIN)
        inv_main.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(
            inv_main,
            text="📦 Control de Inventario y Recetas de Platos",
            font=("Segoe UI", 14, "bold"),
            fg=COLOR_TEXT_DARK,
            bg=COLOR_BG_MAIN,
        ).pack(anchor="w", pady=(0, 10))

        # Cuaderno interno para separar Inventario de Insumos y Recetas
        notebook_inv = ttk.Notebook(inv_main)
        notebook_inv.pack(fill="both", expand=True)

        # Sub-pestaña 1: Insumos de Inventario
        tab_insumos = ttk.Frame(notebook_inv)
        notebook_inv.add(tab_insumos, text="🥕 Insumos y Stock")
        self.init_sub_insumos_tab(tab_insumos)

        # Sub-pestaña 2: Recetas (Asociación Plato -> Ingredientes)
        tab_recetas = ttk.Frame(notebook_inv)
        notebook_inv.add(tab_recetas, text="🍳 Recetas de Platos")
        self.init_sub_recetas_tab(tab_recetas)

    def init_sub_insumos_tab(self, parent):
        container = tk.Frame(parent, bg=COLOR_BG_MAIN)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Panel izquierdo para formulario de gestión (Agregar / Modificar Insumos)
        form_panel = tk.Frame(container, bg=COLOR_CARD, padx=15, pady=15, width=320, highlightbackground="#e2e8f0", highlightthickness=1)
        form_panel.pack(side="left", fill="y", padx=(0, 10))
        form_panel.pack_propagate(False)

        tk.Label(form_panel, text="Gestión de Alimento / Ingrediente", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(anchor="w", pady=(0, 10))

        tk.Label(form_panel, text="NOMBRE DEL ALIMENTO", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        self.inv_nombre = tk.Entry(form_panel, font=("Segoe UI", 9), bg="#f8fafc", relief="solid", bd=1)
        self.inv_nombre.pack(fill="x", pady=(0, 8), ipady=3)

        tk.Label(form_panel, text="CATEGORÍA", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        self.inv_categoria = ttk.Combobox(form_panel, values=["Carnes, Embutidos y Proteínas", "Frutas, Verduras y Frescos", "Lácteos, Refrigerados y Huevos", "Abarrotes, Panadería y Secos", "Bebidas envasadas y complementos", "Otros"], state="readonly")
        self.inv_categoria.pack(fill="x", pady=(0, 8))
        self.inv_categoria.current(0)

        tk.Label(form_panel, text="CANTIDAD / STOCK", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        self.inv_cantidad = tk.Entry(form_panel, font=("Segoe UI", 9), bg="#f8fafc", relief="solid", bd=1)
        self.inv_cantidad.pack(fill="x", pady=(0, 8), ipady=3)

        tk.Label(form_panel, text="UNIDAD DE MEDIDA", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        self.inv_unidad = ttk.Combobox(form_panel, values=["Kg", "Litros", "Unidades", "Gramos", "Libras", "Ml"], state="readonly")
        self.inv_unidad.pack(fill="x", pady=(0, 8))
        self.inv_unidad.current(0)

        tk.Label(form_panel, text="STOCK MÍNIMO (Alerta)", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        self.inv_stock_min = tk.Entry(form_panel, font=("Segoe UI", 9), bg="#f8fafc", relief="solid", bd=1)
        self.inv_stock_min.pack(fill="x", pady=(0, 15), ipady=3)

        btn_box = tk.Frame(form_panel, bg=COLOR_CARD)
        btn_box.pack(fill="x", pady=5)

        tk.Button(btn_box, text="💾 Guardar / Registrar", command=self.guardar_inventario, bg=COLOR_PRIMARY, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(fill="x", pady=3, ipady=3)
        tk.Button(btn_box, text="🗑️ Eliminar Seleccionado", command=self.eliminar_inventario, bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(fill="x", pady=3, ipady=3)
        tk.Button(btn_box, text="🧹 Limpiar Campos", command=self.limpiar_campos_inventario, bg="#64748b", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(fill="x", pady=3, ipady=3)

        # Panel derecho para tabla y buscador de inventario
        table_panel = tk.Frame(container, bg=COLOR_CARD, padx=15, pady=15, highlightbackground="#e2e8f0", highlightthickness=1)
        table_panel.pack(side="right", fill="both", expand=True)

        search_box = tk.Frame(table_panel, bg=COLOR_CARD)
        search_box.pack(fill="x", pady=(0, 10))
        tk.Label(search_box, text="Buscar Alimento:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(side="left", padx=(0, 8))
        self.entry_buscar_inv = tk.Entry(search_box, font=("Segoe UI", 9), width=30, bg="#f8fafc", relief="solid", bd=1)
        self.entry_buscar_inv.pack(side="left", ipady=2)
        self.entry_buscar_inv.bind("<KeyRelease>", self.filtrar_inventario)

        tree_frame_inv = tk.Frame(table_panel, bg=COLOR_CARD)
        tree_frame_inv.pack(fill="both", expand=True)

        columns_inv = ("id", "nombre", "categoria", "cantidad", "unidad", "stock_min")
        self.tree_inv = ttk.Treeview(tree_frame_inv, columns=columns_inv, show="headings", height=15)

        self.tree_inv.heading("id", text="ID")
        self.tree_inv.heading("nombre", text="Alimento / Ingrediente")
        self.tree_inv.heading("categoria", text="Categoría")
        self.tree_inv.heading("cantidad", text="Stock Actual")
        self.tree_inv.heading("unidad", text="Unidad")
        self.tree_inv.heading("stock_min", text="Stock Mínimo")

        self.tree_inv.column("id", width=40, anchor="center")
        self.tree_inv.column("nombre", width=180, anchor="w")
        self.tree_inv.column("categoria", width=140, anchor="center")
        self.tree_inv.column("cantidad", width=80, anchor="center")
        self.tree_inv.column("unidad", width=70, anchor="center")
        self.tree_inv.column("stock_min", width=90, anchor="center")

        scrollbar_inv = ttk.Scrollbar(tree_frame_inv, orient="vertical", command=self.tree_inv.yview)
        self.tree_inv.configure(yscrollcommand=scrollbar_inv.set)

        self.tree_inv.pack(side="left", fill="both", expand=True)
        scrollbar_inv.pack(side="right", fill="y")
        self.tree_inv.bind("<ButtonRelease-1>", self.seleccionar_fila_inventario)

        self.cargar_tabla_inventario()

    def init_sub_recetas_tab(self, parent):
        """Inicializa la sub-pestaña para configurar los ingredientes que lleva cada plato del menú."""
        container = tk.Frame(parent, bg=COLOR_BG_MAIN)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Panel izquierdo: Formulario para asociar ingrediente a plato
        form_receta = tk.Frame(container, bg=COLOR_CARD, padx=15, pady=15, width=340, highlightbackground="#e2e8f0", highlightthickness=1)
        form_receta.pack(side="left", fill="y", padx=(0, 10))
        form_receta.pack_propagate(False)

        tk.Label(form_receta, text="Configurar Receta de Plato", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(anchor="w", pady=(0, 10))

        tk.Label(form_receta, text="SELECCIONAR PLATO DEL MENÚ", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        
        # Lista de platos extraídos del catálogo
        lista_platos_menu = list(self.precios_catalogo.keys())
        self.combo_receta_plato = ttk.Combobox(form_receta, values=lista_platos_menu, state="readonly")
        self.combo_receta_plato.pack(fill="x", pady=(0, 10))
        if lista_platos_menu:
            self.combo_receta_plato.current(0)
        self.combo_receta_plato.bind("<<ComboboxSelected>>", lambda e: self.cargar_tabla_recetas())

        tk.Label(form_receta, text="SELECCIONAR INGREDIENTE", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        self.combo_receta_ingrediente = ttk.Combobox(form_receta, state="readonly")
        self.combo_receta_ingrediente.pack(fill="x", pady=(0, 10))

        tk.Label(form_receta, text="CANTIDAD REQUERIDA", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        self.entry_receta_cantidad = tk.Entry(form_receta, font=("Segoe UI", 9), bg="#f8fafc", relief="solid", bd=1)
        self.entry_receta_cantidad.insert(0, "1.00")
        self.entry_receta_cantidad.pack(fill="x", pady=(0, 15), ipady=3)

        tk.Button(form_receta, text="➕ Agregar Ingrediente a Receta", command=self.guardar_receta_plato, bg=COLOR_PRIMARY, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(fill="x", pady=3, ipady=3)
        tk.Button(form_receta, text="🗑️ Quitar Ingrediente Seleccionado", command=self.eliminar_receta_plato, bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(fill="x", pady=3, ipady=3)

        # Panel derecho: Tabla de ingredientes asociados al plato seleccionado
        table_receta = tk.Frame(container, bg=COLOR_CARD, padx=15, pady=15, highlightbackground="#e2e8f0", highlightthickness=1)
        table_receta.pack(side="right", fill="both", expand=True)

        tk.Label(table_receta, text="Ingredientes Configurados para el Plato", font=("Segoe UI", 10, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 10))

        tree_frame_receta = tk.Frame(table_receta, bg=COLOR_CARD)
        tree_frame_receta.pack(fill="both", expand=True)

        columns_receta = ("id", "plato", "ingrediente", "cantidad", "unidad")
        self.tree_recetas = ttk.Treeview(tree_frame_receta, columns=columns_receta, show="headings", height=15)

        self.tree_recetas.heading("id", text="ID")
        self.tree_recetas.heading("plato", text="Plato")
        self.tree_recetas.heading("ingrediente", text="Ingrediente en Inventario")
        self.tree_recetas.heading("cantidad", text="Cant. Requerida")
        self.tree_recetas.heading("unidad", text="Unidad")

        self.tree_recetas.column("id", width=40, anchor="center")
        self.tree_recetas.column("plato", width=160, anchor="w")
        self.tree_recetas.column("ingrediente", width=160, anchor="w")
        self.tree_recetas.column("cantidad", width=90, anchor="center")
        self.tree_recetas.column("unidad", width=70, anchor="center")

        scrollbar_receta = ttk.Scrollbar(tree_frame_receta, orient="vertical", command=self.tree_recetas.yview)
        self.tree_recetas.configure(yscrollcommand=scrollbar_receta.set)

        self.tree_recetas.pack(side="left", fill="both", expand=True)
        scrollbar_receta.pack(side="right", fill="y")

        self.actualizar_combo_recetas_platos()
        self.cargar_tabla_recetas()

    def actualizar_combo_recetas_platos(self):
        """Carga los nombres de los ingredientes desde la base de datos al combobox de recetas."""
        if not hasattr(self, "combo_receta_ingrediente"):
            return
        db = conectar_db()
        nombres_ingredientes = []
        if db:
            try:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT nombre FROM inventario_alimentos ORDER BY nombre ASC")
                res = cursor.fetchall()
                nombres_ingredientes = [row["nombre"] for row in res]
            except Error as e:
                print(f"Error al cargar ingredientes para recetas: {e}")
            finally:
                db.close()
        
        self.combo_receta_ingrediente["values"] = nombres_ingredientes
        if nombres_ingredientes:
            self.combo_receta_ingrediente.current(0)

    def guardar_receta_plato(self):
        """Asocia un ingrediente y su cantidad requerida a un plato en la base de datos."""
        plato = self.combo_receta_plato.get()
        ingrediente_nombre = self.combo_receta_ingrediente.get()
        cantidad_str = self.entry_receta_cantidad.get().strip()

        if not plato or not ingrediente_nombre or not cantidad_str:
            messagebox.showwarning("Campos Incompletos", "Seleccione un plato, un ingrediente y especifique la cantidad.")
            return

        try:
            cantidad = float(cantidad_str)
            if cantidad <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Valor Inválido", "La cantidad requerida debe ser un número mayor a cero.")
            return

        db = conectar_db()
        if not db:
            return

        try:
            cursor = db.cursor(dictionary=True)
            # Obtener el ID del ingrediente
            cursor.execute("SELECT id FROM inventario_alimentos WHERE nombre = %s", (ingrediente_nombre,))
            ing_res = cursor.fetchone()
            if not ing_res:
                messagebox.showerror("Error", "El ingrediente seleccionado no existe en el inventario.")
                return
            ing_id = ing_res["id"]

            # Verificar si ya existe la relación para actualizar o insertar
            cursor.execute("SELECT id FROM recetas_platos WHERE nombre_plato = %s AND ingrediente_id = %s", (plato, ing_id))
            existente = cursor.fetchone()

            if existente:
                cursor.execute("UPDATE recetas_platos SET cantidad_requerida = %s WHERE id = %s", (cantidad, existente["id"]))
                msg = f"Se actualizó la receta para '{plato}'."
            else:
                cursor.execute("INSERT INTO recetas_platos (nombre_plato, ingrediente_id, cantidad_requerida) VALUES (%s, %s, %s)", (plato, ing_id, cantidad))
                msg = f"Se agregó '{ingrediente_nombre}' a la receta de '{plato}'."

            db.commit()
            messagebox.showinfo("Receta Guardada", msg)
            self.cargar_tabla_recetas()
        except Error as e:
            messagebox.showerror("Error en Base de Datos", f"No se pudo guardar la receta:\n{e}")
        finally:
            db.close()

    def cargar_tabla_recetas(self):
        """Carga en la tabla los ingredientes asociados al plato seleccionado."""
        if not hasattr(self, "tree_recetas"):
            return

        for row in self.tree_recetas.get_children():
            self.tree_recetas.delete(row)

        plato_seleccionado = self.combo_receta_plato.get() if hasattr(self, "combo_receta_plato") else ""

        db = conectar_db()
        if not db:
            return

        try:
            cursor = db.cursor(dictionary=True)
            sql = """
                SELECT r.id, r.nombre_plato, i.nombre as ingrediente_nombre, r.cantidad_requerida, i.unidad 
                FROM recetas_platos r 
                JOIN inventario_alimentos i ON r.ingrediente_id = i.id 
            """
            if plato_seleccionado:
                sql += " WHERE r.nombre_plato = %s"
                cursor.execute(sql, (plato_seleccionado,))
            else:
                cursor.execute(sql)
            
            resultados = cursor.fetchall()
        except Error as e:
            print(f"Error al cargar tabla recetas: {e}")
            resultados = []
        finally:
            db.close()

        for item in resultados:
            self.tree_recetas.insert(
                "",
                "end",
                values=(
                    item.get("id"),
                    item.get("nombre_plato"),
                    item.get("ingrediente_nombre"),
                    item.get("cantidad_requerida"),
                    item.get("unidad")
                )
            )

    def eliminar_receta_plato(self):
        """Elimina la relación de receta seleccionada en la tabla."""
        seleccion = self.tree_recetas.selection()
        if not seleccion:
            messagebox.showwarning("Selección Requerida", "Seleccione un ingrediente de la tabla de recetas para quitar.")
            return

        item_data = self.tree_recetas.item(seleccion[0], "values")
        receta_id = item_data[0]

        if not messagebox.askyesno("Confirmar", "¿Está seguro de quitar este ingrediente de la receta del plato?"):
            return

        db = conectar_db()
        if not db:
            return

        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM recetas_platos WHERE id = %s", (receta_id,))
            db.commit()
            messagebox.showinfo("Eliminado", "El ingrediente fue removido de la receta.")
            self.cargar_tabla_recetas()
        except Error as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")
        finally:
            db.close()

    def cargar_tabla_inventario(self, query=""):
        if not hasattr(self, "tree_inv"):
            return

        for row in self.tree_inv.get_children():
            self.tree_inv.delete(row)

        db = conectar_db()
        if not db:
            return

        try:
            cursor = db.cursor(dictionary=True)
            if query:
                sql = "SELECT * FROM inventario_alimentos WHERE nombre LIKE %s OR categoria LIKE %s"
                cursor.execute(sql, (f"%{query}%", f"%{query}%"))
            else:
                cursor.execute("SELECT * FROM inventario_alimentos")
            resultados = cursor.fetchall()
        except Error as e:
            messagebox.showerror("Error", f"Error al cargar inventario: {e}")
            resultados = []
        finally:
            db.close()

        for item in resultados:
            self.tree_inv.insert(
                "",
                "end",
                values=(
                    item.get("id"),
                    item.get("nombre"),
                    item.get("categoria"),
                    item.get("cantidad"),
                    item.get("unidad"),
                    item.get("stock_min")
                )
            )
        self.actualizar_combo_recetas_platos()

    def filtrar_inventario(self, event):
        texto = self.entry_buscar_inv.get().strip()
        self.cargar_tabla_inventario(texto)

    def limpiar_campos_inventario(self):
        self.inv_nombre.delete(0, tk.END)
        self.inv_categoria.current(0)
        self.inv_cantidad.delete(0, tk.END)
        self.inv_unidad.current(0)
        self.inv_stock_min.delete(0, tk.END)

    def seleccionar_fila_inventario(self, event):
        seleccion = self.tree_inv.selection()
        if not seleccion:
            return
        item_data = self.tree_inv.item(seleccion[0], "values")
        if item_data:
            self.limpiar_campos_inventario()
            self.inv_nombre.insert(0, item_data[1])
            self.inv_categoria.set(item_data[2])
            self.inv_cantidad.insert(0, item_data[3])
            self.inv_unidad.set(item_data[4])
            self.inv_stock_min.insert(0, item_data[5])

    def guardar_inventario(self):
        nombre = self.inv_nombre.get().strip()
        categoria = self.inv_categoria.get()
        cantidad_str = self.inv_cantidad.get().strip()
        unidad = self.inv_unidad.get()
        stock_min_str = self.inv_stock_min.get().strip()

        if not nombre or not cantidad_str or not stock_min_str:
            messagebox.showwarning("Campos Vacíos", "Por favor complete el nombre, la cantidad y el stock mínimo.")
            return

        try:
            cantidad = float(cantidad_str)
            stock_min = float(stock_min_str)
            if cantidad < 0 or stock_min < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Valor Inválido", "La cantidad y el stock mínimo deben ser números válidos mayores o iguales a cero.")
            return

        db = conectar_db()
        if not db:
            return

        try:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM inventario_alimentos WHERE nombre = %s", (nombre,))
            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    "UPDATE inventario_alimentos SET categoria = %s, cantidad = %s, unidad = %s, stock_min = %s WHERE nombre = %s",
                    (categoria, cantidad, unidad, stock_min, nombre)
                )
                msg = f"El alimento '{nombre}' ha sido actualizado exitosamente."
            else:
                cursor.execute(
                    "INSERT INTO inventario_alimentos (nombre, categoria, cantidad, unidad, stock_min) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, categoria, cantidad, unidad, stock_min)
                )
                msg = f"El alimento '{nombre}' ha sido registrado exitosamente en el inventario."

            db.commit()
            messagebox.showinfo("Éxito", msg)
            self.limpiar_campos_inventario()
            self.cargar_tabla_inventario()
        except Error as err:
            messagebox.showerror("Error en Base de Datos", f"No se pudo guardar el alimento:\n{err}")
        finally:
            db.close()

    def eliminar_inventario(self):
        seleccion = self.tree_inv.selection()
        if not seleccion:
            messagebox.showwarning("Selección Requerida", "Seleccione un elemento de la tabla para eliminar.")
            return

        item_data = self.tree_inv.item(seleccion[0], "values")
        nombre_alimento = item_data[1]

        if not messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar el alimento '{nombre_alimento}' del inventario?"):
            return

        db = conectar_db()
        if not db:
            return

        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM inventario_alimentos WHERE nombre = %s", (nombre_alimento,))
            db.commit()
            messagebox.showinfo("Eliminado", f"El alimento '{nombre_alimento}' ha sido eliminado del inventario.")
            self.limpiar_campos_inventario()
            self.cargar_tabla_inventario()
        except Error as err:
            messagebox.showerror("Error", f"No se pudo eliminar el registro:\n{err}")
        finally:
            db.close()

    def init_caja_tab(self):
        caja_main = tk.Frame(self.tab_caja, bg=COLOR_BG_MAIN)
        caja_main.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(
            caja_main,
            text="Pantalla de Cobro, Facturación y Pagos Divididos",
            font=("Segoe UI", 14, "bold"),
            fg=COLOR_TEXT_DARK,
            bg=COLOR_BG_MAIN,
        ).pack(anchor="w", pady=(0, 10))

        caja_container = tk.Frame(caja_main, bg=COLOR_BG_MAIN)
        caja_container.pack(fill="both", expand=True)

        left_caja = tk.Frame(caja_container, bg=COLOR_CARD, padx=15, pady=15, highlightbackground="#e2e8f0", highlightthickness=1)
        left_caja.pack(side="left", fill="both", expand=True, padx=(0, 10))

        header_selector_caja = tk.Frame(left_caja, bg=COLOR_CARD)
        header_selector_caja.pack(fill="x", pady=(0, 10))

        tk.Label(header_selector_caja, text="SELECCIONAR CUENTA / MESA:", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w")
        
        self.combo_caja_ubicacion = ttk.Combobox(header_selector_caja, width=28, state="readonly", font=("Segoe UI", 9))
        self.combo_caja_ubicacion.pack(anchor="w", pady=(2, 0))
        self.combo_caja_ubicacion.bind("<<ComboboxSelected>>", lambda e: self.actualizar_vista_caja())

        self.lbl_info_caja_servicio = tk.Label(left_caja, text="Servicio: Mesa", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
        self.lbl_info_caja_servicio.pack(anchor="w", pady=(5, 10))

        self.frame_items_caja = tk.Frame(left_caja, bg=COLOR_CARD)
        self.frame_items_caja.pack(fill="both", expand=True, pady=5)

        right_caja = tk.Frame(caja_container, bg=COLOR_CARD, width=350, padx=20, pady=20, highlightbackground="#e2e8f0", highlightthickness=1)
        right_caja.pack(side="right", fill="y")
        right_caja.pack_propagate(False)

        tk.Label(right_caja, text="Resumen de Cobro", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 15))

        self.lbl_caja_total_pagar = tk.Label(right_caja, text="Total a Pagar: $0.00", font=("Segoe UI", 14, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY)
        self.lbl_caja_total_pagar.pack(anchor="w", pady=(0, 5))

        self.lbl_caja_saldo_pendiente = tk.Label(right_caja, text="Saldo Pendiente: $0.00", font=("Segoe UI", 10, "bold"), bg=COLOR_CARD, fg="#ef4444")
        self.lbl_caja_saldo_pendiente.pack(anchor="w", pady=(0, 20))

        btn_frame_pago = tk.Frame(right_caja, bg=COLOR_CARD)
        btn_frame_pago.pack(fill="x", pady=10)

        tk.Button(
            btn_frame_pago,
            text="💳 Pago Completo",
            command=self.cobrar_pedido_completo,
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        ).pack(fill="x", pady=(0, 10))

        tk.Button(
            btn_frame_pago,
            text="✂️ Pago Dividido (Entre comensales)",
            command=self.abrir_pago_dividido,
            bg="#0ea5e9",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        ).pack(fill="x")

    def actualizar_combos_caja(self):
        ubicaciones_activas = [k for k, v in self.pedidos_por_ubicacion.items() if v.get("items") or v.get("total", 0) > 0]
        if not ubicaciones_activas:
            ubicaciones_activas = ["Mesa #1"]
            
        self.combo_caja_ubicacion["values"] = ubicaciones_activas
        current = self.combo_caja_ubicacion.get()
        if current not in ubicaciones_activas:
            self.combo_caja_ubicacion.set(ubicaciones_activas[0])

    def obtener_estado_caja_actual(self):
        key = self.combo_caja_ubicacion.get() if hasattr(self, "combo_caja_ubicacion") and self.combo_caja_ubicacion.get() else "Mesa #1"
        if key not in self.pedidos_por_ubicacion:
            self.pedidos_por_ubicacion[key] = {
                "tipo_servicio": "Mesa",
                "ubicacion": key,
                "items": [],
                "nota": "",
                "total": 0.0,
                "saldo_pendiente": 0.0,
                "hora_llegada": None,
                "orden_numero": None,
                "enviado_cocina": False
            }
        return self.pedidos_por_ubicacion[key]

    def actualizar_vista_caja(self):
        for widget in self.frame_items_caja.winfo_children():
            widget.destroy()

        estado = self.obtener_estado_caja_actual()
        tipo = estado.get("tipo_servicio", "Mesa")
        ubicacion = estado.get("ubicacion", "Mesa #1")
        items = estado.get("items", [])
        total = estado.get("total", 0.0)
        saldo = estado.get("saldo_pendiente", 0.0)

        if tipo == "Mesa":
            self.lbl_info_caja_servicio.config(text=f"Servicio: {tipo} | {ubicacion}")
        else:
            self.lbl_info_caja_servicio.config(text=f"Servicio: {tipo}")
            
        self.lbl_caja_total_pagar.config(text=f"Total Cuenta: ${total:.2f}")
        self.lbl_caja_saldo_pendiente.config(text=f"Saldo Pendiente: ${saldo:.2f}")

        if not items and total == 0.0:
            tk.Label(self.frame_items_caja, text="No hay un pedido activo para esta ubicación.\nGenere uno desde la pestaña 'Pedidos'.", font=("Segoe UI", 9, "italic"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, justify="center").pack(pady=50)
            return

        for item in items:
            sub = item["precio"] * item["cantidad"]
            row = tk.Frame(self.frame_items_caja, bg=COLOR_CARD)
            row.pack(fill="x", pady=3)

            txt = f"{item['nombre']} (x{item['cantidad']})" if item['cantidad'] > 1 else item['nombre']
            tk.Label(row, text=txt, font=("Segoe UI", 9), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(side="left")
            tk.Label(row, text=f"${sub:.2f}", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(side="right")

        if tipo == "Para llevar":
            row_ext = tk.Frame(self.frame_items_caja, bg=COLOR_CARD)
            row_ext.pack(fill="x", pady=3)
            tk.Label(row_ext, text="📦 Cubiertos Desechables", font=("Segoe UI", 9, "italic"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(side="left")
            tk.Label(row_ext, text="$0.50", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(side="right")
        elif tipo == "Delivery":
            row_ext = tk.Frame(self.frame_items_caja, bg=COLOR_CARD)
            row_ext.pack(fill="x", pady=3)
            tk.Label(row_ext, text="📦 Costo de Envío / Carrera", font=("Segoe UI", 9, "italic"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(side="left")
            tk.Label(row_ext, text="$2.00", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(side="right")

    def cobrar_pedido_completo(self):
        estado = self.obtener_estado_caja_actual()
        saldo = estado.get("saldo_pendiente", 0.0)
        if saldo <= 0.0:
            messagebox.showwarning("Sin Saldo", "No hay saldo pendiente por cobrar para esta ubicación o el pedido no ha sido enviado a cocina.")
            return
        
        self.preguntar_tipo_comprobante(saldo, "Completo")

    def preguntar_tipo_comprobante(self, monto, tipo_transaccion):
        top = tk.Toplevel(self.root)
        top.title("Seleccionar Comprobante de Venta")
        centrar_ventana(top, 380, 240)
        top.config(bg=COLOR_CARD)
        top.resizable(False, False)

        tk.Label(
            top,
            text="Tipo de Comprobante de Venta",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_DARK
        ).pack(pady=15)

        tk.Label(
            top,
            text="¿Desea emitir Factura o Consumidor Final?",
            font=("Segoe UI", 9),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED
        ).pack(pady=(0, 15))

        def elegir_opcion(opcion):
            top.destroy()
            if opcion == "Factura":
                self.pedir_datos_factura(monto, tipo_transaccion)
            else:
                self.seleccionar_metodo_pago(monto, tipo_transaccion, "Consumidor Final")

        btn_factura = tk.Button(
            top,
            text="📄 FACTURA (Con datos)",
            command=lambda: elegir_opcion("Factura"),
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2"
        )
        btn_factura.pack(fill="x", padx=30, pady=5, ipady=5)

        btn_cf = tk.Button(
            top,
            text="👤 CONSUMIDOR FINAL",
            command=lambda: elegir_opcion("Consumidor Final"),
            bg="#64748b",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2"
        )
        btn_cf.pack(fill="x", padx=30, pady=5, ipady=5)

    def pedir_datos_factura(self, monto, tipo_transaccion):
        top = tk.Toplevel(self.root)
        top.title("Datos para la Factura")
        centrar_ventana(top, 360, 420)
        top.config(bg=COLOR_CARD)
        top.resizable(False, False)

        tk.Label(top, text="Ingrese los datos de Facturación", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(pady=15)

        tk.Label(top, text="RUC / Cédula:", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=25)
        ent_ruc = tk.Entry(top, font=("Segoe UI", 9), relief="solid", bd=1)
        ent_ruc.pack(fill="x", padx=25, pady=2, ipady=3)

        tk.Label(top, text="Razón Social / Nombre:", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=25)
        ent_nombre = tk.Entry(top, font=("Segoe UI", 9), relief="solid", bd=1)
        ent_nombre.pack(fill="x", padx=25, pady=2, ipady=3)

        tk.Label(top, text="Dirección:", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=25)
        ent_dir = tk.Entry(top, font=("Segoe UI", 9), relief="solid", bd=1)
        ent_dir.pack(fill="x", padx=25, pady=2, ipady=3)

        tk.Label(top, text="Correo Electrónico:", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=25)
        ent_correo = tk.Entry(top, font=("Segoe UI", 9), relief="solid", bd=1)
        ent_correo.pack(fill="x", padx=25, pady=2, ipady=3)

        tk.Label(top, text="Teléfono:", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=25)
        ent_telefono = tk.Entry(top, font=("Segoe UI", 9), relief="solid", bd=1)
        ent_telefono.pack(fill="x", padx=25, pady=2, ipady=3)

        def continuar():
            ruc = ent_ruc.get().strip()
            nom = ent_nombre.get().strip()
            dir_cli = ent_dir.get().strip()
            correo = ent_correo.get().strip()
            telefono = ent_telefono.get().strip()
            if not ruc or not nom:
                messagebox.showwarning("Campos Vacíos", "RUC/Cédula y Nombre son obligatorios.")
                return
            top.destroy()
            datos_factura = {
                "ruc": ruc, 
                "nombre": nom, 
                "direccion": dir_cli if dir_cli else "N/A",
                "correo": correo if correo else "N/A",
                "telefono": telefono if telefono else "N/A"
            }
            self.seleccionar_metodo_pago(monto, tipo_transaccion, "Factura", datos_factura)

        tk.Button(top, text="Continuar al Pago", command=continuar, bg=COLOR_PRIMARY, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(pady=15, ipadx=10, ipady=5)

    def seleccionar_metodo_pago(self, monto, tipo_transaccion, tipo_comprobante="Consumidor Final", datos_factura=None):
        top = tk.Toplevel(self.root)
        top.title("Seleccionar Método de Pago")
        centrar_ventana(top, 360, 260)
        top.config(bg=COLOR_CARD)
        top.resizable(False, False)

        tk.Label(
            top, 
            text=f"Monto a Cobrar: ${monto:.2f}", 
            font=("Segoe UI", 11, "bold"), 
            bg=COLOR_CARD, 
            fg=COLOR_TEXT_DARK
        ).pack(pady=15)

        tk.Label(
            top, 
            text="Seleccione la forma de pago:", 
            font=("Segoe UI", 9, "bold"), 
            bg=COLOR_CARD, 
            fg=COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=25, pady=(0, 5))

        metodo_var = tk.StringVar(value="Efectivo")
        
        opciones_frame = tk.Frame(top, bg=COLOR_CARD)
        opciones_frame.pack(fill="x", padx=25, pady=5)

        for metodo in ["Efectivo", "Tarjeta", "Transferencia"]:
            tk.Radiobutton(
                opciones_frame, 
                text=metodo, 
                variable=metodo_var, 
                value=metodo, 
                font=("Segoe UI", 9), 
                bg=COLOR_CARD, 
                fg=COLOR_TEXT_DARK,
                cursor="hand2"
            ).pack(anchor="w", pady=2)

        def confirmar_cobro():
            metodo_elegido = metodo_var.get()
            top.destroy()
            if metodo_elegido == "Efectivo":
                self.abrir_calculadora_efectivo(monto, tipo_transaccion, tipo_comprobante, datos_factura)
            else:
                self.procesar_pago(tipo_transaccion, monto, metodo_elegido, tipo_comprobante, datos_factura)

        tk.Button(
            top, 
            text="Confirmar y Procesar Cobro", 
            command=confirmar_cobro, 
            bg=COLOR_PRIMARY, 
            fg="white", 
            font=("Segoe UI", 9, "bold"), 
            relief="flat", 
            cursor="hand2"
        ).pack(pady=15, ipadx=10, ipady=5)

    def abrir_calculadora_efectivo(self, monto_a_cobrar, tipo_transaccion, tipo_comprobante="Consumidor Final", datos_factura=None):
        top = tk.Toplevel(self.root)
        top.title("Cobro en Efectivo - Billetes y Monedas")
        centrar_ventana(top, 650, 550)
        top.config(bg=COLOR_BG_MAIN)
        top.resizable(False, False)

        tk.Label(
            top,
            text=f"Monto a Pagar: ${monto_a_cobrar:.2f}",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_BG_MAIN,
            fg=COLOR_PRIMARY
        ).pack(pady=10)

        content_frame = tk.Frame(top, bg=COLOR_BG_MAIN)
        content_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Columna Billetes
        f_billetes = tk.Frame(content_frame, bg="#065f46", padx=10, pady=10)
        f_billetes.pack(side="left", fill="both", expand=True, padx=(0, 5))

        tk.Label(f_billetes, text="BILLETES", font=("Segoe UI", 10, "bold"), bg="#065f46", fg="white").pack(pady=(0, 8))
        entries_b = {}
        for denom in [100, 50, 20, 10, 5, 1]:
            row = tk.Frame(f_billetes, bg="#065f46")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"$ {denom}", font=("Segoe UI", 9, "bold"), bg="#065f46", fg="white", width=6, anchor="w").pack(side="left")
            ent = tk.Entry(row, font=("Segoe UI", 9), justify="center", relief="solid", bd=1)
            ent.insert(0, "0")
            ent.pack(side="right", fill="x", expand=True, ipady=2)
            entries_b[denom] = ent

        # Columna Monedas
        f_monedas = tk.Frame(content_frame, bg="#581c87", padx=10, pady=10)
        f_monedas.pack(side="left", fill="both", expand=True, padx=(5, 0))

        tk.Label(f_monedas, text="MONEDAS", font=("Segoe UI", 10, "bold"), bg="#581c87", fg="white").pack(pady=(0, 8))
        entries_m = {}
        for denom in [1.00, 0.50, 0.25, 0.10, 0.05, 0.01]:
            row = tk.Frame(f_monedas, bg="#581c87")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"$ {denom:.2f}", font=("Segoe UI", 9, "bold"), bg="#581c87", fg="white", width=6, anchor="w").pack(side="left")
            ent = tk.Entry(row, font=("Segoe UI", 9), justify="center", relief="solid", bd=1)
            ent.insert(0, "0")
            ent.pack(side="right", fill="x", expand=True, ipady=2)
            entries_m[denom] = ent

        f_bottom = tk.Frame(top, bg=COLOR_CARD, padx=15, pady=15, highlightbackground="#e2e8f0", highlightthickness=1)
        f_bottom.pack(fill="x", padx=15, pady=15)

        lbl_recibido = tk.Label(f_bottom, text="Total Recibido: $0.00", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK)
        lbl_recibido.pack(anchor="w")

        lbl_cambio = tk.Label(f_bottom, text="Cambio / Vuelto: $0.00", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg="#10b981")
        lbl_cambio.pack(anchor="w", pady=(2, 10))

        def calcular_cambio(*args):
            total_recibido = 0.0
            for d, e in entries_b.items():
                try:
                    total_recibido += d * int(e.get().strip() or 0)
                except ValueError:
                    pass
            for d, e in entries_m.items():
                try:
                    total_recibido += d * int(e.get().strip() or 0)
                except ValueError:
                    pass
            
            cambio = round(total_recibido - monto_a_cobrar, 2)
            lbl_recibido.config(text=f"Total Recibido: ${total_recibido:.2f}")
            if cambio >= 0:
                lbl_cambio.config(text=f"Cambio / Vuelto: ${cambio:.2f}", fg="#10b981")
            else:
                lbl_cambio.config(text=f"Faltan: ${abs(cambio):.2f}", fg="#ef4444")
            return total_recibido, cambio

        for ent in entries_b.values():
            ent.bind("<KeyRelease>", calcular_cambio)
        for ent in entries_m.values():
            ent.bind("<KeyRelease>", calcular_cambio)

        def procesar_efectivo_final():
            recibido, cambio = calcular_cambio()
            if recibido < monto_a_cobrar:
                messagebox.showerror("Monto Insuficiente", "El efectivo recibido es menor al monto total a pagar.")
                return
            top.destroy()
            self.procesar_pago(tipo_transaccion, monto_a_cobrar, "Efectivo", tipo_comprobante, datos_factura)

        tk.Button(
            f_bottom,
            text="Confirmar Cobro en Efectivo",
            command=procesar_efectivo_final,
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(fill="x", ipady=5)

    def simular_impresion_factura(self, monto, metodo, tipo_comprobante, datos_factura):
        top = tk.Toplevel(self.root)
        top.title("Simulación de Factura Electrónica")
        centrar_ventana(top, 420, 560)
        top.config(bg="white")
        top.resizable(False, False)

        f_content = tk.Frame(top, bg="white", padx=20, pady=20)
        f_content.pack(fill="both", expand=True)

        tk.Label(f_content, text="☕ CAFETERÍA - RESTAURANTE POS", font=("Segoe UI", 11, "bold"), bg="white", fg=COLOR_TEXT_DARK).pack()
        tk.Label(f_content, text="RUC: 1102938475001 | Matriz: Loja, Ecuador", font=("Segoe UI", 8), bg="white", fg=COLOR_TEXT_MUTED).pack(pady=(0, 10))
        
        num_factura = f"001-001-{random.randint(1, 999999):06d}"
        tk.Label(f_content, text=f"FACTURA N° {num_factura}", font=("Segoe UI", 10, "bold"), bg="white", fg=COLOR_PRIMARY).pack(anchor="w")
        tk.Label(f_content, text=f"Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", font=("Segoe UI", 8), bg="white", fg=COLOR_TEXT_MUTED).pack(anchor="w")
        tk.Label(f_content, text=f"Método de Pago: {metodo}", font=("Segoe UI", 8), bg="white", fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        f_cliente = tk.Frame(f_content, bg="#f8fafc", padx=10, pady=8, highlightbackground="#e2e8f0", highlightthickness=1)
        f_cliente.pack(fill="x", pady=(0, 10))
        
        if tipo_comprobante == "Factura" and datos_factura:
            tk.Label(f_cliente, text=f"Razón Social: {datos_factura['nombre']}", font=("Segoe UI", 8, "bold"), bg="#f8fafc", fg=COLOR_TEXT_DARK).pack(anchor="w")
            tk.Label(f_cliente, text=f"RUC/Cédula: {datos_factura['ruc']}", font=("Segoe UI", 8), bg="#f8fafc", fg=COLOR_TEXT_DARK).pack(anchor="w")
            tk.Label(f_cliente, text=f"Dirección: {datos_factura['direccion']}", font=("Segoe UI", 8), bg="#f8fafc", fg=COLOR_TEXT_DARK).pack(anchor="w")
            tk.Label(f_cliente, text=f"Correo: {datos_factura.get('correo', 'N/A')}", font=("Segoe UI", 8), bg="#f8fafc", fg=COLOR_TEXT_DARK).pack(anchor="w")
            tk.Label(f_cliente, text=f"Teléfono: {datos_factura.get('telefono', 'N/A')}", font=("Segoe UI", 8), bg="#f8fafc", fg=COLOR_TEXT_DARK).pack(anchor="w")
        else:
            tk.Label(f_cliente, text="Razón Social: CONSUMIDOR FINAL", font=("Segoe UI", 8, "bold"), bg="#f8fafc", fg=COLOR_TEXT_DARK).pack(anchor="w")
            tk.Label(f_cliente, text="RUC/Cédula: 9999999999999", font=("Segoe UI", 8), bg="#f8fafc", fg=COLOR_TEXT_DARK).pack(anchor="w")

        tk.Label(f_content, text="--- DETALLE DE LA TRANSACCIÓN ---", font=("Segoe UI", 8, "bold"), bg="white", fg=COLOR_TEXT_MUTED).pack(pady=5)
        
        estado = self.obtener_estado_caja_actual()
        for item in estado.get("items", []):
            sub = item["precio"] * item["cantidad"]
            lbl_item = tk.Label(f_content, text=f"{item['cantidad']}x {item['nombre']} ....... ${sub:.2f}", font=("Segoe UI", 8), bg="white", fg=COLOR_TEXT_DARK)
            lbl_item.pack(anchor="w")

        tk.Frame(f_content, height=1, bg="#cbd5e1").pack(fill="x", pady=10)

        subtotal = round(monto / 1.15, 2)
        iva = round(monto - subtotal, 2)

        tk.Label(f_content, text=f"SUBTOTAL 15%: ${subtotal:.2f}", font=("Segoe UI", 8), bg="white", fg=COLOR_TEXT_DARK).pack(anchor="e")
        tk.Label(f_content, text=f"IVA 15%: ${iva:.2f}", font=("Segoe UI", 8), bg="white", fg=COLOR_TEXT_DARK).pack(anchor="e")
        tk.Label(f_content, text=f"VALOR TOTAL: ${monto:.2f}", font=("Segoe UI", 11, "bold"), bg="white", fg=COLOR_PRIMARY).pack(anchor="e", pady=(5, 10))

        tk.Label(f_content, text="¡Gracias por su compra! Comprobante Autorizado por el SRI.", font=("Segoe UI", 7, "italic"), bg="white", fg=COLOR_TEXT_MUTED).pack(pady=5)

        tk.Button(
            f_content,
            text="Imprimir / Cerrar Factura",
            command=top.destroy,
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(fill="x", pady=10, ipady=3)

    def procesar_pago(self, tipo_pago, monto, metodo="Efectivo", tipo_comprobante="Consumidor Final", datos_factura=None):
        estado = self.obtener_estado_caja_actual()
        saldo_actual = estado.get("saldo_pendiente", 0.0)
        nuevo_saldo = round(saldo_actual - monto, 2)
        if nuevo_saldo < 0:
            nuevo_saldo = 0.0
            
        estado["saldo_pendiente"] = nuevo_saldo

        # Registrar la venta en las variables de sesión para conectar la Caja con el Cierre de Caja
        self.ventas_totales_sesion += monto
        if metodo == "Efectivo":
            self.ventas_efectivo_sesion += monto

        self.simular_impresion_factura(monto, metodo, tipo_comprobante, datos_factura)

        if nuevo_saldo <= 0.0:
            if estado.get("tipo_servicio") == "Mesa":
                mesa_str = estado.get("ubicacion", "Mesa #1")
                try:
                    numero_mesa = int(mesa_str.split("#")[1])
                    db = conectar_db()
                    if db:
                        cursor = db.cursor()
                        cursor.execute("UPDATE mesas SET estado = 'Por limpiar' WHERE numero = %s", (numero_mesa,))
                        db.commit()
                        db.close()
                except Exception as e:
                    print(f"Error actualizando mesa a por limpiar: {e}")

            messagebox.showinfo(
                "Transacción Exitosa", 
                f"Pago procesado con éxito.\nModalidad: {tipo_pago}\nMétodo: {metodo}\nComprobante: {tipo_comprobante}\nMonto cobrado: ${monto:.2f}\n\n¡Cuenta totalmente pagada! Mesa marcada como POR LIMPIAR."
            )
            self.pedidos_por_ubicacion[estado["ubicacion"]] = {
                "tipo_servicio": estado["tipo_servicio"],
                "ubicacion": estado["ubicacion"],
                "items": [],
                "nota": "",
                "total": 0.0,
                "saldo_pendiente": 0.0,
                "hora_llegada": None,
                "orden_numero": None,
                "enviado_cocina": False
            }
        else:
            messagebox.showinfo(
                "Pago Parcial Exitoso", 
                f"Se ha cobrado una parte de la cuenta.\nModalidad: {tipo_pago}\nMétodo: {metodo}\nComprobante: {tipo_comprobante}\nMonto cobrado: ${monto:.2f}\n\n¡Aún queda un saldo pendiente de ${nuevo_saldo:.2f} por cobrar!"
            )

        self.actualizar_combos_caja()
        self.actualizar_vista_caja()
        self.actualizar_vista_carrito()

    def abrir_pago_dividido(self):
        estado = self.obtener_estado_caja_actual()
        saldo = estado.get("saldo_pendiente", 0.0)
        if saldo <= 0.0:
            messagebox.showwarning("Sin Saldo", "No hay un saldo pendiente para dividir en la caja o el pedido no ha sido enviado a cocina.")
            return

        top = tk.Toplevel(self.root)
        top.title("Motor de Pagos Divididos")
        centrar_ventana(top, 360, 260)
        top.config(bg=COLOR_CARD)
        top.resizable(False, False)

        tk.Label(top, text=f"Dividir Saldo Pendiente (${saldo:.2f})", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(pady=15)
        
        tk.Label(top, text="Número de Personas / Partes a Pagar Ahora:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=20)
        entry_partes = tk.Entry(top, font=("Segoe UI", 10), relief="solid", bd=1)
        entry_partes.pack(fill="x", padx=20, pady=5, ipady=3)

        def calcular_division():
            try:
                partes = int(entry_partes.get().strip())
                if partes <= 0:
                    raise ValueError()
                resultado = saldo / partes
                top.destroy()
                self.preguntar_tipo_comprobante(resultado, f"Dividido (Parte de {partes} comensales)")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido de partes.")

        tk.Button(top, text="Calcular Monto por Persona", command=calcular_division, bg=COLOR_PRIMARY, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(pady=15, ipadx=10, ipady=5)

    def init_apertura_tab(self):
        apertura_main = tk.Frame(self.tab_apertura, bg=COLOR_BG_MAIN)
        apertura_main.pack(fill="both", expand=True, padx=15, pady=15)

        card_apertura = tk.Frame(
            apertura_main,
            bg=COLOR_CARD,
            padx=20,
            pady=20,
            highlightbackground="#e2e8f0",
            highlightthickness=1,
        )
        card_apertura.pack(fill="both", expand=True)

        header_banner = tk.Frame(card_apertura, bg="#7f1d1d", padx=15, pady=12)
        header_banner.pack(fill="x", pady=(0, 20))

        tk.Label(
            header_banner,
            text="🔒 APERTURA DE CAJA",
            font=("Segoe UI", 12, "bold"),
            bg="#7f1d1d",
            fg="white",
        ).pack(anchor="w")

        tk.Label(
            header_banner,
            text="Ingrese la cantidad de cada denominación para registrar el fondo inicial",
            font=("Segoe UI", 9),
            bg="#7f1d1d",
            fg="#fecaca",
        ).pack(anchor="w", pady=(2, 0))

        content_split = tk.Frame(card_apertura, bg=COLOR_CARD)
        content_split.pack(fill="both", expand=True)

        # Billetes
        frame_billetes_outer = tk.Frame(content_split, bg="#065f46", padx=15, pady=15)
        frame_billetes_outer.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(frame_billetes_outer, text="BILLETES", font=("Segoe UI", 11, "bold"), bg="#065f46", fg="white").pack(anchor="center", pady=(0, 10))

        self.entries_billetes = {}
        denominaciones_billetes = [100, 50, 20, 10, 5, 1]

        for denom in denominaciones_billetes:
            row_b = tk.Frame(frame_billetes_outer, bg="#065f46")
            row_b.pack(fill="x", pady=4)
            tk.Label(row_b, text=f"$ {denom}", font=("Segoe UI", 10, "bold"), bg="#065f46", fg="white", width=8, anchor="w").pack(side="left")
            ent = tk.Entry(row_b, font=("Segoe UI", 10), bg="white", fg=COLOR_TEXT_DARK, justify="center", relief="solid", bd=1)
            ent.insert(0, "0")
            ent.pack(side="right", fill="x", expand=True, ipady=3)
            
            def hacer_callback_billete(e, entry_widget=ent):
                self.calcular_totales_apertura()
                if e.char and e.char.isdigit():
                    val_actual = entry_widget.get()
                    if val_actual == "0":
                        entry_widget.delete(0, tk.END)

            ent.bind("<KeyPress>", hacer_callback_billete)
            ent.bind("<KeyRelease>", lambda e: self.calcular_totales_apertura())
            self.entries_billetes[denom] = ent

        sub_b_frame = tk.Frame(frame_billetes_outer, bg="#1e3a8a", padx=10, pady=8)
        sub_b_frame.pack(fill="x", pady=(15, 0))
        tk.Label(sub_b_frame, text="SUBTOTAL BILLETES", font=("Segoe UI", 8, "bold"), bg="#1e3a8a", fg="#93c5fd").pack(anchor="w")
        self.lbl_subtotal_billetes = tk.Label(sub_b_frame, text="$0.00", font=("Segoe UI", 14, "bold"), bg="#1e3a8a", fg="white")
        self.lbl_subtotal_billetes.pack(anchor="w")

        # Monedas
        frame_monedas_outer = tk.Frame(content_split, bg="#581c87", padx=15, pady=15)
        frame_monedas_outer.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(frame_monedas_outer, text="MONEDAS", font=("Segoe UI", 11, "bold"), bg="#581c87", fg="white").pack(anchor="center", pady=(0, 10))

        self.entries_monedas = {}
        denominaciones_monedas = [1.00, 0.50, 0.25, 0.10, 0.05, 0.01]

        for denom in denominaciones_monedas:
            row_m = tk.Frame(frame_monedas_outer, bg="#581c87")
            row_m.pack(fill="x", pady=4)
            tk.Label(row_m, text=f"$ {denom:.2f}", font=("Segoe UI", 10, "bold"), bg="#581c87", fg="white", width=8, anchor="w").pack(side="left")
            ent = tk.Entry(row_m, font=("Segoe UI", 10), bg="white", fg=COLOR_TEXT_DARK, justify="center", relief="solid", bd=1)
            ent.insert(0, "0")
            ent.pack(side="right", fill="x", expand=True, ipady=3)
            ent.bind("<KeyRelease>", lambda e: self.calcular_totales_apertura())
            self.entries_monedas[denom] = ent

        sub_m_frame = tk.Frame(frame_monedas_outer, bg="#312e81", padx=10, pady=8)
        sub_m_frame.pack(fill="x", pady=(15, 0))
        tk.Label(sub_m_frame, text="SUBTOTAL MONEDAS", font=("Segoe UI", 8, "bold"), bg="#312e81", fg="#c7d2fe").pack(anchor="w")
        self.lbl_subtotal_monedas = tk.Label(sub_m_frame, text="$0.00", font=("Segoe UI", 14, "bold"), bg="#312e81", fg="white")
        self.lbl_subtotal_monedas.pack(anchor="w")

        # Totales y Botones
        frame_totales_right = tk.Frame(content_split, bg="#1e293b", padx=15, pady=15, width=280)
        frame_totales_right.pack(side="right", fill="y")
        frame_totales_right.pack_propagate(False)

        tk.Label(frame_totales_right, text="TOTAL APERTURA", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#94a3b8").pack(anchor="w")
        self.lbl_total_apertura = tk.Label(frame_totales_right, text="$0.00", font=("Segoe UI", 22, "bold"), bg="#1e293b", fg="#ef4444")
        self.lbl_total_apertura.pack(anchor="w", pady=(5, 25))

        btn_guardar = tk.Button(frame_totales_right, text="💾 GUARDAR", command=self.guardar_apertura_caja, bg="#1e3a8a", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", height=2)
        btn_guardar.pack(fill="x", pady=(0, 10))

        btn_abrir_caja = tk.Button(frame_totales_right, text="ABRIR CAJA", command=self.ejecutar_apertura_caja, bg="#d97706", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", height=2)
        btn_abrir_caja.pack(fill="x", pady=(0, 15))

        tk.Label(frame_totales_right, text="⚠️ Todos los campos son obligatorios. Ingrese 0 si no tiene esa denominación.", font=("Segoe UI", 8, "italic"), bg="#1e293b", fg="#94a3b8", wraplength=250, justify="left").pack(anchor="w")

    def calcular_totales_apertura(self):
        subtotal_b = 0.0
        for denom, entry in self.entries_billetes.items():
            try:
                val = int(entry.get().strip() or 0)
                subtotal_b += denom * val
            except ValueError:
                pass

        subtotal_m = 0.0
        for denom, entry in self.entries_monedas.items():
            try:
                val = int(entry.get().strip() or 0)
                subtotal_m += denom * val
            except ValueError:
                pass

        total_general = subtotal_b + subtotal_m
        self.lbl_subtotal_billetes.config(text=f"${subtotal_b:.2f}")
        self.lbl_subtotal_monedas.config(text=f"${subtotal_m:.2f}")
        self.lbl_total_apertura.config(text=f"${total_general:.2f}")

    def guardar_apertura_caja(self):
        self.calcular_totales_apertura()
        total_texto = self.lbl_total_apertura.cget("text")
        messagebox.showinfo("Fondo Guardado", f"El desglose del fondo inicial por un total de {total_texto} ha sido guardado correctamente.")

    def ejecutar_apertura_caja(self):
        self.calcular_totales_apertura()
        total_texto = self.lbl_total_apertura.cget("text")
        if total_texto == "$0.00":
            if not messagebox.askyesno("Apertura en $0.00", "¿Está seguro de abrir la caja sin fondo inicial?"):
                return

        # Se registra el fondo inicial para conectarlo con la Caja y el Cierre de Caja
        self.fondo_inicial_caja = float(total_texto.replace("$", ""))
        self.ventas_efectivo_sesion = 0.0
        self.ventas_totales_sesion = 0.0
        if hasattr(self, "tab_cierre"):
            self.actualizar_resumen_cierre()

        messagebox.showinfo("Caja Abierta", f"¡Caja abierta exitosamente con un fondo inicial de {total_texto}!")

    def init_cierre_tab(self):
        cierre_main = tk.Frame(self.tab_cierre, bg=COLOR_BG_MAIN)
        cierre_main.pack(fill="both", expand=True, padx=15, pady=15)

        card_cierre = tk.Frame(
            cierre_main,
            bg=COLOR_CARD,
            padx=20,
            pady=20,
            highlightbackground="#e2e8f0",
            highlightthickness=1,
        )
        card_cierre.pack(fill="both", expand=True)

        header_banner = tk.Frame(card_cierre, bg="#7f1d1d", padx=15, pady=12)
        header_banner.pack(fill="x", pady=(0, 20))

        tk.Label(
            header_banner,
            text="🔐 CIERRE DE CAJA",
            font=("Segoe UI", 12, "bold"),
            bg="#7f1d1d",
            fg="white",
        ).pack(anchor="w")

        tk.Label(
            header_banner,
            text="Ingrese la cantidad de cada denominación contada para registrar el cierre",
            font=("Segoe UI", 9),
            bg="#7f1d1d",
            fg="#fecaca",
        ).pack(anchor="w", pady=(2, 0))

        nombre_val = self.usuario.get('nombre', 'Usuario')
        tk.Label(
            header_banner,
            text=f"👤 Responsable del cierre: {nombre_val}",
            font=("Segoe UI", 9, "bold"),
            bg="#7f1d1d",
            fg="white",
        ).pack(anchor="w", pady=(8, 0))

        content_split = tk.Frame(card_cierre, bg=COLOR_CARD)
        content_split.pack(fill="both", expand=True)

        # Billetes
        frame_billetes_outer = tk.Frame(content_split, bg="#065f46", padx=15, pady=15)
        frame_billetes_outer.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(frame_billetes_outer, text="BILLETES", font=("Segoe UI", 11, "bold"), bg="#065f46", fg="white").pack(anchor="center", pady=(0, 10))

        self.entries_billetes_cierre = {}
        denominaciones_billetes = [100, 50, 20, 10, 5, 1]

        for denom in denominaciones_billetes:
            row_b = tk.Frame(frame_billetes_outer, bg="#065f46")
            row_b.pack(fill="x", pady=4)
            tk.Label(row_b, text=f"$ {denom}", font=("Segoe UI", 10, "bold"), bg="#065f46", fg="white", width=8, anchor="w").pack(side="left")
            ent = tk.Entry(row_b, font=("Segoe UI", 10), bg="white", fg=COLOR_TEXT_DARK, justify="center", relief="solid", bd=1)
            ent.insert(0, "0")
            ent.pack(side="right", fill="x", expand=True, ipady=3)

            def hacer_callback_billete_cierre(e, entry_widget=ent):
                self.calcular_totales_cierre()
                if e.char and e.char.isdigit():
                    val_actual = entry_widget.get()
                    if val_actual == "0":
                        entry_widget.delete(0, tk.END)

            ent.bind("<KeyPress>", hacer_callback_billete_cierre)
            ent.bind("<KeyRelease>", lambda e: self.calcular_totales_cierre())
            self.entries_billetes_cierre[denom] = ent

        sub_b_frame = tk.Frame(frame_billetes_outer, bg="#1e3a8a", padx=10, pady=8)
        sub_b_frame.pack(fill="x", pady=(15, 0))
        tk.Label(sub_b_frame, text="SUBTOTAL BILLETES", font=("Segoe UI", 8, "bold"), bg="#1e3a8a", fg="#93c5fd").pack(anchor="w")
        self.lbl_subtotal_billetes_cierre = tk.Label(sub_b_frame, text="$0.00", font=("Segoe UI", 14, "bold"), bg="#1e3a8a", fg="white")
        self.lbl_subtotal_billetes_cierre.pack(anchor="w")

        # Monedas
        frame_monedas_outer = tk.Frame(content_split, bg="#581c87", padx=15, pady=15)
        frame_monedas_outer.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(frame_monedas_outer, text="MONEDAS", font=("Segoe UI", 11, "bold"), bg="#581c87", fg="white").pack(anchor="center", pady=(0, 10))

        self.entries_monedas_cierre = {}
        denominaciones_monedas = [1.00, 0.50, 0.25, 0.10, 0.05, 0.01]

        for denom in denominaciones_monedas:
            row_m = tk.Frame(frame_monedas_outer, bg="#581c87")
            row_m.pack(fill="x", pady=4)
            tk.Label(row_m, text=f"$ {denom:.2f}", font=("Segoe UI", 10, "bold"), bg="#581c87", fg="white", width=8, anchor="w").pack(side="left")
            ent = tk.Entry(row_m, font=("Segoe UI", 10), bg="white", fg=COLOR_TEXT_DARK, justify="center", relief="solid", bd=1)
            ent.insert(0, "0")
            ent.pack(side="right", fill="x", expand=True, ipady=3)
            ent.bind("<KeyRelease>", lambda e: self.calcular_totales_cierre())
            self.entries_monedas_cierre[denom] = ent

        sub_m_frame = tk.Frame(frame_monedas_outer, bg="#312e81", padx=10, pady=8)
        sub_m_frame.pack(fill="x", pady=(15, 0))
        tk.Label(sub_m_frame, text="SUBTOTAL MONEDAS", font=("Segoe UI", 8, "bold"), bg="#312e81", fg="#c7d2fe").pack(anchor="w")
        self.lbl_subtotal_monedas_cierre = tk.Label(sub_m_frame, text="$0.00", font=("Segoe UI", 14, "bold"), bg="#312e81", fg="white")
        self.lbl_subtotal_monedas_cierre.pack(anchor="w")

        # Totales y Botones
        frame_totales_right = tk.Frame(content_split, bg="#1e293b", padx=15, pady=15, width=280)
        frame_totales_right.pack(side="right", fill="y")
        frame_totales_right.pack_propagate(False)

        # Resumen conectado con los datos reales de Apertura de Caja y Caja / Cobro
        tk.Label(frame_totales_right, text="🔗 DATOS DE LA CAJA", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#38bdf8").pack(anchor="w")

        tk.Label(frame_totales_right, text="Fondo Inicial (Apertura)", font=("Segoe UI", 8), bg="#1e293b", fg="#94a3b8").pack(anchor="w", pady=(8, 0))
        self.lbl_cierre_fondo_inicial = tk.Label(frame_totales_right, text="$0.00", font=("Segoe UI", 12, "bold"), bg="#1e293b", fg="white")
        self.lbl_cierre_fondo_inicial.pack(anchor="w")

        tk.Label(frame_totales_right, text="Ventas en Efectivo (Caja)", font=("Segoe UI", 8), bg="#1e293b", fg="#94a3b8").pack(anchor="w", pady=(6, 0))
        self.lbl_cierre_ventas_efectivo = tk.Label(frame_totales_right, text="$0.00", font=("Segoe UI", 12, "bold"), bg="#1e293b", fg="white")
        self.lbl_cierre_ventas_efectivo.pack(anchor="w")

        tk.Label(frame_totales_right, text="Total Esperado en Caja", font=("Segoe UI", 8), bg="#1e293b", fg="#94a3b8").pack(anchor="w", pady=(6, 0))
        self.lbl_cierre_total_esperado = tk.Label(frame_totales_right, text="$0.00", font=("Segoe UI", 12, "bold"), bg="#1e293b", fg="#38bdf8")
        self.lbl_cierre_total_esperado.pack(anchor="w", pady=(0, 12))

        tk.Frame(frame_totales_right, height=1, bg="#334155").pack(fill="x", pady=(0, 12))

        tk.Label(frame_totales_right, text="TOTAL CONTADO", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#94a3b8").pack(anchor="w")
        self.lbl_total_cierre = tk.Label(frame_totales_right, text="$0.00", font=("Segoe UI", 20, "bold"), bg="#1e293b", fg="#ef4444")
        self.lbl_total_cierre.pack(anchor="w", pady=(5, 10))

        tk.Label(frame_totales_right, text="DIFERENCIA", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#94a3b8").pack(anchor="w")
        self.lbl_cierre_diferencia = tk.Label(frame_totales_right, text="$0.00", font=("Segoe UI", 14, "bold"), bg="#1e293b", fg="white")
        self.lbl_cierre_diferencia.pack(anchor="w", pady=(2, 15))

        btn_guardar = tk.Button(frame_totales_right, text="💾 GUARDAR", command=self.guardar_cierre_caja, bg="#1e3a8a", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", height=2)
        btn_guardar.pack(fill="x", pady=(0, 10))

        btn_cerrar_caja = tk.Button(frame_totales_right, text="CERRAR CAJA", command=self.ejecutar_cierre_caja, bg="#d97706", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", height=2)
        btn_cerrar_caja.pack(fill="x", pady=(0, 15))

        tk.Label(frame_totales_right, text="⚠️ Todos los campos son obligatorios. Ingrese 0 si no tiene esa denominación.", font=("Segoe UI", 8, "italic"), bg="#1e293b", fg="#94a3b8", wraplength=250, justify="left").pack(anchor="w")

        self.actualizar_resumen_cierre()

    def actualizar_resumen_cierre(self):
        """Refresca en la pestaña de Cierre los datos reales tomados de Apertura de Caja y Caja / Cobro."""
        if not hasattr(self, "lbl_cierre_fondo_inicial"):
            return

        total_esperado = self.fondo_inicial_caja + self.ventas_efectivo_sesion
        self.lbl_cierre_fondo_inicial.config(text=f"${self.fondo_inicial_caja:.2f}")
        self.lbl_cierre_ventas_efectivo.config(text=f"${self.ventas_efectivo_sesion:.2f}")
        self.lbl_cierre_total_esperado.config(text=f"${total_esperado:.2f}")
        self.calcular_totales_cierre()

    def calcular_totales_cierre(self):
        subtotal_b = 0.0
        for denom, entry in self.entries_billetes_cierre.items():
            try:
                val = int(entry.get().strip() or 0)
                subtotal_b += denom * val
            except ValueError:
                pass

        subtotal_m = 0.0
        for denom, entry in self.entries_monedas_cierre.items():
            try:
                val = int(entry.get().strip() or 0)
                subtotal_m += denom * val
            except ValueError:
                pass

        total_general = subtotal_b + subtotal_m
        self.lbl_subtotal_billetes_cierre.config(text=f"${subtotal_b:.2f}")
        self.lbl_subtotal_monedas_cierre.config(text=f"${subtotal_m:.2f}")
        self.lbl_total_cierre.config(text=f"${total_general:.2f}")

        total_esperado = self.fondo_inicial_caja + self.ventas_efectivo_sesion
        diferencia = round(total_general - total_esperado, 2)
        if diferencia == 0:
            self.lbl_cierre_diferencia.config(text="$0.00 (Cuadrada)", fg="#10b981")
        elif diferencia > 0:
            self.lbl_cierre_diferencia.config(text=f"+${diferencia:.2f} (Sobrante)", fg="#facc15")
        else:
            self.lbl_cierre_diferencia.config(text=f"-${abs(diferencia):.2f} (Faltante)", fg="#ef4444")

    def guardar_cierre_caja(self):
        self.calcular_totales_cierre()
        total_texto = self.lbl_total_cierre.cget("text")
        nombre_val = self.usuario.get('nombre', 'Usuario')
        messagebox.showinfo("Conteo Guardado", f"El desglose del cierre por un total de {total_texto} ha sido guardado correctamente.\nRegistrado por: {nombre_val}")

    def ejecutar_cierre_caja(self):
        self.calcular_totales_cierre()
        total_texto = self.lbl_total_cierre.cget("text")
        total_valor = float(total_texto.replace("$", ""))
        total_esperado = round(self.fondo_inicial_caja + self.ventas_efectivo_sesion, 2)
        diferencia = round(total_valor - total_esperado, 2)

        if total_texto == "$0.00":
            if not messagebox.askyesno("Cierre en $0.00", "¿Está seguro de cerrar la caja sin efectivo contado?"):
                return

        nombre_val = self.usuario.get('nombre', 'Usuario')
        cedula_val = self.usuario.get('cedula', '')

        db = conectar_db()
        if db:
            try:
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO cierres_caja (usuario_cedula, usuario_nombre, fecha_hora, total_contado, fondo_inicial, ventas_efectivo, diferencia) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (cedula_val, nombre_val, datetime.now(), total_valor, self.fondo_inicial_caja, self.ventas_efectivo_sesion, diferencia)
                )
                db.commit()
            except Error as err:
                messagebox.showerror("Error de Base de Datos", f"No se pudo registrar el cierre de caja:\n{err}")
                return
            finally:
                db.close()

        messagebox.showinfo(
            "Caja Cerrada",
            f"¡Caja cerrada exitosamente con un total contado de {total_texto}!\n"
            f"Total esperado (Fondo + Ventas en Efectivo): ${total_esperado:.2f}\n"
            f"Diferencia: ${diferencia:.2f}\n"
            f"Registrado por: {nombre_val}"
        )

        # Se reinician los valores de la sesión de caja tras un cierre exitoso
        self.fondo_inicial_caja = 0.0
        self.ventas_efectivo_sesion = 0.0
        self.ventas_totales_sesion = 0.0
        self.actualizar_resumen_cierre()

    def init_admin_tab(self):
        admin_main = tk.Frame(self.tab_admin, bg=COLOR_BG_MAIN)
        admin_main.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(admin_main, text="Administración de Empleados y Accesos", font=("Segoe UI", 14, "bold"), fg=COLOR_TEXT_DARK, bg=COLOR_BG_MAIN).pack(anchor="w", pady=(0, 10))

        main_container = tk.Frame(admin_main, bg=COLOR_BG_MAIN)
        main_container.pack(fill="both", expand=True)

        left_panel = tk.Frame(main_container, bg=COLOR_CARD, padx=15, pady=15, highlightbackground="#e2e8f0", highlightthickness=1)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(left_panel, text="Datos del Empleado", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(anchor="w", pady=(0, 10))

        fields_config = [
            ("CÉDULA", "reg_cedula", False),
            ("NOMBRE COMPLETO", "reg_nombre", False),
            ("CONTRASEÑA", "reg_clave", True),
            ("PIN DE ACCESO", "reg_pin", True),
        ]

        for label_text, attr_name, is_password in fields_config:
            tk.Label(left_panel, text=label_text, font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
            entry = tk.Entry(left_panel, font=("Segoe UI", 9), width=22, bg="#f8fafc", show="•" if is_password else "", relief="solid", bd=1)
            entry.pack(anchor="w", pady=(0, 6), ipady=3)
            setattr(self, attr_name, entry)

        tk.Label(left_panel, text="ROL EN EL SISTEMA", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 1))
        self.reg_rol = ttk.Combobox(left_panel, values=["Administrador", "Cajero", "Cocinero", "Mesero"], width=20, state="readonly")
        self.reg_rol.pack(anchor="w", pady=(0, 15))
        self.reg_rol.current(0)

        btn_box = tk.Frame(left_panel, bg=COLOR_CARD)
        btn_box.pack(fill="x", pady=5)

        tk.Button(btn_box, text="💾 Registrar Empleado", command=self.registrar_empleado, bg=COLOR_PRIMARY, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(fill="x", pady=3, ipady=3)
        tk.Button(btn_box, text="🗑️ Eliminar Seleccionado", command=self.eliminar_empleado, bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(fill="x", pady=3, ipady=3)
        tk.Button(btn_box, text="🧹 Limpiar Campos", command=self.limpiar_campos_admin, bg="#64748b", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(fill="x", pady=3, ipady=3)

        right_panel = tk.Frame(main_container, bg=COLOR_CARD, padx=15, pady=15, highlightbackground="#e2e8f0", highlightthickness=1)
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(right_panel, text="Empleados Registrados", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 10))

        tree_frame = tk.Frame(right_panel, bg=COLOR_CARD)
        tree_frame.pack(fill="both", expand=True)

        columns = ("id", "cedula", "nombre", "rol", "pin")
        self.tree_usuarios = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)

        self.tree_usuarios.heading("id", text="ID")
        self.tree_usuarios.heading("cedula", text="Cédula")
        self.tree_usuarios.heading("nombre", text="Nombre Completo")
        self.tree_usuarios.heading("rol", text="Rol")
        self.tree_usuarios.heading("pin", text="PIN")

        self.tree_usuarios.column("id", width=40, anchor="center")
        self.tree_usuarios.column("cedula", width=100, anchor="center")
        self.tree_usuarios.column("nombre", width=180, anchor="w")
        self.tree_usuarios.column("rol", width=110, anchor="center")
        self.tree_usuarios.column("pin", width=60, anchor="center")

        scrollbar_usuarios = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscrollcommand=scrollbar_usuarios.set)

        self.tree_usuarios.pack(side="left", fill="both", expand=True)
        scrollbar_usuarios.pack(side="right", fill="y")
        self.tree_usuarios.bind("<ButtonRelease-1>", self.seleccionar_fila_usuario)

        self.cargar_tabla_usuarios()

    def cargar_tabla_usuarios(self):
        for row in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(row)

        db = conectar_db()
        if not db:
            return
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT id, cedula, nombre, rol, pin FROM usuarios")
            usuarios = cursor.fetchall()
        except Error as e:
            messagebox.showerror("Error", f"No se pudo cargar usuarios: {e}")
            usuarios = []
        finally:
            db.close()

        for u in usuarios:
            self.tree_usuarios.insert(
                "",
                "end",
                values=(u["id"], u["cedula"], u["nombre"], u["rol"], u["pin"])
            )

    def limpiar_campos_admin(self):
        self.reg_cedula.delete(0, tk.END)
        self.reg_nombre.delete(0, tk.END)
        self.reg_clave.delete(0, tk.END)
        self.reg_pin.delete(0, tk.END)
        self.reg_rol.current(0)

    def seleccionar_fila_usuario(self, event):
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            return
        item_data = self.tree_usuarios.item(seleccion[0], "values")
        if item_data:
            self.limpiar_campos_admin()
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT * FROM usuarios WHERE id = %s", (item_data[0],))
                u = cursor.fetchone()
                db.close()
                if u:
                    self.reg_cedula.insert(0, u.get("cedula", ""))
                    self.reg_nombre.insert(0, u.get("nombre", ""))
                    self.reg_clave.insert(0, u.get("clave", ""))
                    self.reg_pin.insert(0, u.get("pin", ""))
                    self.reg_rol.set(u.get("rol", "Administrador"))

    def registrar_empleado(self):
        cedula = self.reg_cedula.get().strip()
        nombre = self.reg_nombre.get().strip()
        clave = self.reg_clave.get().strip()
        pin = self.reg_pin.get().strip()
        rol = self.reg_rol.get()

        if not cedula or not nombre or not clave or not pin:
            messagebox.showwarning("Campos Vacíos", "Por favor complete todos los campos obligatorios.")
            return

        db = conectar_db()
        if not db:
            return

        try:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE cedula = %s", (cedula,))
            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    "UPDATE usuarios SET nombre = %s, clave = %s, pin = %s, rol = %s WHERE cedula = %s",
                    (nombre, clave, pin, rol, cedula)
                )
                msg = f"El empleado '{nombre}' ha sido actualizado correctamente."
            else:
                cursor.execute(
                    "INSERT INTO usuarios (cedula, nombre, clave, pin, rol) VALUES (%s, %s, %s, %s, %s)",
                    (cedula, nombre, clave, pin, rol)
                )
                msg = f"El empleado '{nombre}' ha sido registrado exitosamente."

            db.commit()
            messagebox.showinfo("Éxito", msg)
            self.limpiar_campos_admin()
            self.cargar_tabla_usuarios()
        except Error as err:
            messagebox.showerror("Error de Base de Datos", f"No se pudo guardar el empleado:\n{err}")
        finally:
            db.close()

    def eliminar_empleado(self):
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            messagebox.showwarning("Selección Requerida", "Seleccione un empleado de la tabla para eliminar.")
            return

        item_data = self.tree_usuarios.item(seleccion[0], "values")
        id_usuario = item_data[0]
        nombre_usuario = item_data[2]

        if not messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al empleado '{nombre_usuario}'?"):
            return

        db = conectar_db()
        if not db:
            return

        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
            db.commit()
            messagebox.showinfo("Eliminado", f"El empleado '{nombre_usuario}' ha sido eliminado.")
            self.limpiar_campos_admin()
            self.cargar_tabla_usuarios()
        except Error as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")
        finally:
            db.close()


# Bloque principal para la ejecución inicial de la aplicación levantando la ventana de Login.
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()