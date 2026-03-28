import sqlite3
import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox  # Importamos messagebox para alertas visuales

# --- CONFIGURACIÓN DE BASE DE DATOS ---
def iniciar_db():
    conn = sqlite3.connect('voley_club.db')
    cursor = conn.cursor()
    # Tablas con integridad referencial
    cursor.execute('''CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT NOT NULL, apodo_dorsal TEXT, posicion TEXT, contacto TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS asistencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT, dni_integrante TEXT, fecha DATE, estado TEXT,
        FOREIGN KEY(dni_integrante) REFERENCES integrantes(dni))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS finanzas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, dni_integrante TEXT, concepto TEXT,
        monto_total REAL, abonos REAL, saldo_pendiente REAL,
        FOREIGN KEY(dni_integrante) REFERENCES integrantes(dni))''')
    conn.commit()
    conn.close()

def calcular_asistencia_7_dias(dni):
    try:
        conn = sqlite3.connect('voley_club.db')
        cursor = conn.cursor()
        hace_una_semana = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('''SELECT COUNT(*) FROM asistencia 
                          WHERE dni_integrante = ? AND fecha >= ? AND estado = "Asistió"''', 
                       (dni, hace_una_semana))
        resultado = cursor.fetchone()[0]
        conn.close()
        return resultado
    except Exception: return 0

# --- INTERFAZ GRÁFICA ---
class AppVoley(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Voley Club Manager v1.2")
        self.geometry("900x650")
        
        # Configuración estética
        self.fuente_titulos = ("Montserrat", 20, "bold")
        self.fuente_texto = ("Montserrat", 12)

        # --- SISTEMA DE PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_registro = self.tabview.add("Registro y Gestión")
        self.tab_lista = self.tabview.add("Lista de Integrantes")
        self.tab_finanzas = self.tabview.add("Pagos y Deudas")

        # Inicialización de interfaces
        self.setup_ui_registro()
        self.setup_gestion_diaria()
        self.setup_tabla_visualizacion()
        self.setup_finanzas()

    # --- PESTAÑA 1: REGISTRO ---
    def setup_ui_registro(self):
        ctk.CTkLabel(self.tab_registro, text="Nuevo Integrante", font=self.fuente_titulos).pack(pady=10)
        
        self.entry_dni = ctk.CTkEntry(self.tab_registro, placeholder_text="DNI / ID Único", width=300)
        self.entry_dni.pack(pady=5)

        self.entry_nombre = ctk.CTkEntry(self.tab_registro, placeholder_text="Nombre Completo", width=300)
        self.entry_nombre.pack(pady=5)

        self.combobox_posicion = ctk.CTkComboBox(self.tab_registro, values=["Punta", "Central", "Armador", "Líbero", "Opuesto"], width=300)
        self.combobox_posicion.pack(pady=5)

        ctk.CTkButton(self.tab_registro, text="Registrar Jugador", command=self.guardar_jugador).pack(pady=10)

    def setup_gestion_diaria(self):
        self.frame_gestion = ctk.CTkFrame(self.tab_registro)
        self.frame_gestion.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(self.frame_gestion, text="Control Diario (Use el DNI de arriba)", font=self.fuente_texto).pack(pady=5)

        self.btn_frame = ctk.CTkFrame(self.frame_gestion, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        # Botones de acción
        ctk.CTkButton(self.btn_frame, text="Asistió", fg_color="#28a745", width=100,
                      command=lambda: self.registrar_evento_db("Asistió")).grid(row=0, column=0, padx=5)
        ctk.CTkButton(self.btn_frame, text="Falta ($10)", fg_color="#dc3545", width=100,
                      command=lambda: self.registrar_evento_db("Falta", 10.0)).grid(row=0, column=1, padx=5)
        ctk.CTkButton(self.btn_frame, text="Tardanza ($5)", fg_color="#fd7e14", width=100,
                      command=lambda: self.registrar_evento_db("Tardanza", 5.0)).grid(row=0, column=2, padx=5)

    # --- PESTAÑA 2: LISTA ---
    def setup_tabla_visualizacion(self):
        # Estilo de tabla
        style = ttk.Style()
        style.theme_use("default")
        
        # Configuración del cuerpo de la tabla
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        fieldbackground="#2b2b2b", 
                        rowheight=25)
        
        style.configure("Treeview.Heading", 
                        background="#333333", 
                        foreground="black", 
                        font=("Montserrat", 10, "bold"))
        
        style.map("Treeview", background=[('selected', '#1f538d')])

        self.tabla = ttk.Treeview(self.tab_lista, columns=("DNI", "Nombre", "Posición", "Asistencias"), show="headings")
        for col in ("DNI", "Nombre", "Posición", "Asistencias"):
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center")
        self.tabla.pack(pady=10, padx=10, fill="both", expand=True)

        # Evento: Al hacer clic en la tabla, se ejecuta 'cargar_seleccion'
        self.tabla.bind("<<TreeviewSelect>>", self.cargar_seleccion)

        # Frame para botones de edición
        self.frame_edicion = ctk.CTkFrame(self.tab_lista)
        self.frame_edicion.pack(pady=10, padx=20, fill="x")

        # Botones alineados
        self.btn_actualizar_lista = ctk.CTkButton(self.frame_edicion, text="Refrescar Tabla", command=self.cargar_datos)
        self.btn_actualizar_lista.grid(row=0, column=0, padx=10, pady=10)

        self.btn_editar = ctk.CTkButton(self.frame_edicion, text="Guardar Cambios", fg_color="#f0ad4e", command=self.editar_jugador)
        self.btn_editar.grid(row=0, column=1, padx=10, pady=10)

        self.btn_eliminar = ctk.CTkButton(self.frame_edicion, text="Eliminar Integrante", fg_color="#d9534f", command=self.eliminar_jugador)
        self.btn_eliminar.grid(row=0, column=2, padx=10, pady=10)
        
    # --- PESTAÑA 3: FINANZAS ---
    def setup_finanzas(self):
        ctk.CTkLabel(self.tab_finanzas, text="Control de Deudas", font=self.fuente_titulos).pack(pady=10)

        self.frame_cobro = ctk.CTkFrame(self.tab_finanzas)
        self.frame_cobro.pack(pady=10, padx=20, fill="x")

        self.entry_pago = ctk.CTkEntry(self.frame_cobro, placeholder_text="Monto a abonar ($)", width=150)
        self.entry_pago.grid(row=0, column=0, padx=10, pady=10)

        ctk.CTkButton(self.frame_cobro, text="Registrar Pago", fg_color="#007bff", 
                      command=self.registrar_pago).grid(row=0, column=1, padx=10, pady=10)

        self.tabla_deudas = ttk.Treeview(self.tab_finanzas, columns=("DNI", "Nombre", "Deuda"), show="headings")
        for col in ("DNI", "Nombre", "Deuda"):
            self.tabla_deudas.heading(col, text=col)
        self.tabla_deudas.pack(pady=10, padx=10, fill="both", expand=True)

        ctk.CTkButton(self.tab_finanzas, text="Actualizar Saldos", command=self.cargar_finanzas).pack(pady=5)

    # --- LÓGICA DE BASE DE DATOS ---
    def guardar_jugador(self):
        dni, nombre, pos = self.entry_dni.get(), self.entry_nombre.get(), self.combobox_posicion.get()
        if not dni or not nombre:
            messagebox.showwarning("Atención", "DNI y Nombre son obligatorios")
            return

        conn = sqlite3.connect('voley_club.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO integrantes (dni, nombre, posicion) VALUES (?, ?, ?)", (dni, nombre, pos))
            conn.commit()
            messagebox.showinfo("Éxito", f"{nombre} ha sido registrado.")
            self.cargar_datos()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Este DNI ya está registrado.")
        finally:
            conn.close()

    def registrar_evento_db(self, tipo_evento, monto=0):
        dni = self.entry_dni.get()
        if not dni:
            messagebox.showwarning("DNI faltante", "Por favor ingresa un DNI en la parte superior.")
            return
        
        conn = sqlite3.connect('voley_club.db')
        cursor = conn.cursor()
        # Verificar si el jugador existe
        cursor.execute("SELECT nombre FROM integrantes WHERE dni=?", (dni,))
        if not cursor.fetchone():
            messagebox.showerror("Error", "El DNI no existe en la base de datos.")
            return

        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO asistencia (dni_integrante, fecha, estado) VALUES (?, ?, ?)", (dni, fecha_hoy, tipo_evento))
        
        if monto > 0:
            cursor.execute("INSERT INTO finanzas (dni_integrante, concepto, monto_total, abonos, saldo_pendiente) VALUES (?, ?, ?, 0, ?)", 
                           (dni, f"Multa: {tipo_evento}", monto, monto))
        conn.commit()
        conn.close()
        messagebox.showinfo("Registro", f"Evento '{tipo_evento}' guardado.")

    def cargar_datos(self):
        for item in self.tabla.get_children(): self.tabla.delete(item)
        conn = sqlite3.connect('voley_club.db')
        cursor = conn.cursor()
        cursor.execute("SELECT dni, nombre, posicion FROM integrantes")
        for fila in cursor.fetchall():
            asist = calcular_asistencia_7_dias(fila[0])
            self.tabla.insert("", "end", values=(fila[0], fila[1], fila[2], asist))
        conn.close()

    def cargar_finanzas(self):
        for item in self.tabla_deudas.get_children(): self.tabla_deudas.delete(item)
        conn = sqlite3.connect('voley_club.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT i.dni, i.nombre, SUM(f.monto_total - f.abonos) 
                          FROM integrantes i LEFT JOIN finanzas f ON i.dni = f.dni_integrante
                          GROUP BY i.dni''')
        for fila in cursor.fetchall():
            saldo = fila[2] if fila[2] is not None else 0.0
            self.tabla_deudas.insert("", "end", values=(fila[0], fila[1], f"$ {saldo:.2f}"))
        conn.close()

    def registrar_pago(self):
        seleccion = self.tabla_deudas.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Elige un jugador de la tabla primero.")
            return
            
        try:
            monto_pago = float(self.entry_pago.get())
            dni_jugador = self.tabla_deudas.item(seleccion)['values'][0]
            
            conn = sqlite3.connect('voley_club.db')
            cursor = conn.cursor()
            # Registramos el abono como un valor negativo en saldo_pendiente
            cursor.execute("INSERT INTO finanzas (dni_integrante, concepto, monto_total, abonos, saldo_pendiente) VALUES (?, 'ABONO REALIZADO', 0, ?, ?)", 
                           (dni_jugador, monto_pago, -monto_pago))
            conn.commit()
            conn.close()
            
            self.entry_pago.delete(0, 'end')
            self.cargar_finanzas()
            messagebox.showinfo("Pago", "Abono registrado correctamente.")
        except ValueError:
            messagebox.showerror("Error", "Ingresa un monto numérico válido.")
            
    def cargar_seleccion(self, event):
        """Carga los datos de la fila seleccionada en los campos de la Pestaña 1"""
        seleccion = self.tabla.selection()
        if not seleccion: return
        
        datos = self.tabla.item(seleccion)['values']
        # Llenamos los campos de la pestaña de registro para poder editarlos
        self.entry_dni.delete(0, 'end')
        self.entry_dni.insert(0, datos[0])
        self.entry_nombre.delete(0, 'end')
        self.entry_nombre.insert(0, datos[1])
        self.combobox_posicion.set(datos[2])
        
        # Opcional: Cambiar a la pestaña de registro automáticamente
        # self.tabview.set("Registro y Gestión")

    def editar_jugador(self):
        dni = self.entry_dni.get()
        nombre = self.entry_nombre.get()
        posicion = self.combobox_posicion.get()

        if messagebox.askyesno("Confirmar", f"¿Deseas actualizar los datos de {nombre}?"):
            conn = sqlite3.connect('voley_club.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE integrantes SET nombre=?, posicion=? WHERE dni=?", (nombre, posicion, dni))
            conn.commit()
            conn.close()
            self.cargar_datos()
            messagebox.showinfo("Éxito", "Datos actualizados correctamente.")

    def eliminar_jugador(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona a alguien de la tabla primero.")
            return

        dni = self.tabla.item(seleccion)['values'][0]
        nombre = self.tabla.item(seleccion)['values'][1]

        if messagebox.askyesnocancel("Peligro", f"¿ESTÁS SEGURO? Esto eliminará a {nombre} y todo su historial de pagos y asistencia."):
            conn = sqlite3.connect('voley_club.db')
            cursor = conn.cursor()
            # Eliminamos en cascada manualmente (o podrías configurar la DB para hacerlo)
            cursor.execute("DELETE FROM asistencia WHERE dni_integrante=?", (dni,))
            cursor.execute("DELETE FROM finanzas WHERE dni_integrante=?", (dni,))
            cursor.execute("DELETE FROM integrantes WHERE dni=?", (dni,))
            conn.commit()
            conn.close()
            self.cargar_datos()
            self.cargar_finanzas()
            messagebox.showinfo("Eliminado", "Integrante borrado permanentemente.")

if __name__ == "__main__":
    iniciar_db()
    app = AppVoley()
    app.mainloop()