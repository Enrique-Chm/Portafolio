import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import sqlite3
import pandas as pd
import os
from datetime import datetime

class SQLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aprende SQL - Versión Mejorada")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Configurar estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Variables
        self.db_path = "ejemplo.db"
        self.conexion = None
        self.cursor = None
        self.current_csv_data = None
        self.field_entries = {}

        # Conectar a la base de datos
        self.conectar_db()

        # Crear interfaz
        self.create_widgets()

        # Configurar el cierre de la aplicación
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def conectar_db(self):
        """Conectar a la base de datos SQLite"""
        try:
            self.conexion = sqlite3.connect(self.db_path)
            self.cursor = self.conexion.cursor()
            # Habilitar claves foráneas
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.conexion.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Error SQL", f"Error en la consulta:\n{str(e)}")
            self.update_status("Error en consulta SQL")

    def create_widgets(self):
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(
            main_frame,
            text="Aprende SQL - Herramienta Interactiva",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 10))

        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # Pestañas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(pady=10, expand=True, fill=tk.BOTH)

        # Crear pestañas
        self.create_csv_tab()
        self.create_table_tab()
        self.create_insert_tab()
        self.create_query_tab()
        self.create_view_tab()
        self.create_export_tab()

        # Después de crear pestañas, poblar combos
        self.actualizar_tablas()
        self.update_status("Aplicación iniciada correctamente")

    def create_csv_tab(self):
        """Pestaña para cargar archivos CSV"""
        self.tab_csv = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_csv, text="📁 Cargar CSV")

        csv_frame = ttk.LabelFrame(self.tab_csv, text="Carga de Archivos CSV", padding="10")
        csv_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(csv_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.btn_cargar_csv = ttk.Button(
            btn_frame,
            text="Seleccionar archivo CSV",
            command=self.cargar_csv
        )
        self.btn_cargar_csv.pack(side=tk.LEFT)

        self.label_csv = ttk.Label(
            csv_frame,
            text="Ningún archivo seleccionado",
            foreground="gray"
        )
        self.label_csv.pack(anchor=tk.W, pady=(0, 10))

        options_frame = ttk.LabelFrame(csv_frame, text="Opciones de carga", padding="5")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(options_frame, text="Nombre de la tabla:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.entry_tabla_csv = ttk.Entry(options_frame, width=20)
        self.entry_tabla_csv.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        self.entry_tabla_csv.insert(0, "datos")

        self.var_replace = tk.BooleanVar(value=True)
        self.chk_replace = ttk.Checkbutton(
            options_frame,
            text="Reemplazar tabla si existe",
            variable=self.var_replace
        )
        self.chk_replace.grid(row=0, column=2, sticky=tk.W)

        self.btn_procesar_csv = ttk.Button(
            options_frame,
            text="Cargar a base de datos",
            command=self.procesar_csv,
            state=tk.DISABLED
        )
        self.btn_procesar_csv.grid(row=1, column=0, columnspan=3, pady=10)

        preview_frame = ttk.LabelFrame(csv_frame, text="Vista previa", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_csv = ttk.Treeview(preview_frame)
        scrollbar_csv = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree_csv.yview)
        self.tree_csv.configure(yscrollcommand=scrollbar_csv.set)

        self.tree_csv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_csv.pack(side=tk.RIGHT, fill=tk.Y)

    def create_table_tab(self):
        """Pestaña para crear tablas"""
        self.tab_table = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_table, text="🔧 Crear Tabla")

        table_frame = ttk.LabelFrame(self.tab_table, text="Creación de Tablas", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        name_frame = ttk.Frame(table_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(name_frame, text="Nombre de la tabla:").pack(side=tk.LEFT)
        self.entry_tabla_nombre = ttk.Entry(name_frame, width=30)
        self.entry_tabla_nombre.pack(side=tk.LEFT, padx=(10, 0))

        columns_frame = ttk.LabelFrame(table_frame, text="Definir columnas", padding="5")
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.tree_columns = ttk.Treeview(
            columns=('Nombre', 'Tipo', 'Restricciones'),
            show='headings',
            height=8
        )
        self.tree_columns.heading('Nombre', text='Nombre')
        self.tree_columns.heading('Tipo', text='Tipo')
        self.tree_columns.heading('Restricciones', text='Restricciones')

        self.tree_columns.column('Nombre', width=150)
        self.tree_columns.column('Tipo', width=100)
        self.tree_columns.column('Restricciones', width=200)

        self.tree_columns.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_cols = ttk.Scrollbar(columns_frame, orient=tk.VERTICAL, command=self.tree_columns.yview)
        self.tree_columns.configure(yscrollcommand=scrollbar_cols.set)
        scrollbar_cols.pack(side=tk.RIGHT, fill=tk.Y)

        add_col_frame = ttk.Frame(table_frame)
        add_col_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(add_col_frame, text="Nombre:").grid(row=0, column=0, padx=(0, 5))
        self.entry_col_nombre = ttk.Entry(add_col_frame, width=15)
        self.entry_col_nombre.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(add_col_frame, text="Tipo:").grid(row=0, column=2, padx=(0, 5))
        self.combo_tipo = ttk.Combobox(
            add_col_frame,
            values=['INTEGER', 'TEXT', 'REAL', 'BLOB'],
            width=10
        )
        self.combo_tipo.grid(row=0, column=3, padx=(0, 10))
        self.combo_tipo.set('TEXT')

        self.var_primary = tk.BooleanVar()
        self.var_not_null = tk.BooleanVar()
        self.var_unique = tk.BooleanVar()

        ttk.Checkbutton(add_col_frame, text="PRIMARY KEY", variable=self.var_primary).grid(row=0, column=4, padx=(0, 5))
        ttk.Checkbutton(add_col_frame, text="NOT NULL", variable=self.var_not_null).grid(row=0, column=5, padx=(0, 5))
        ttk.Checkbutton(add_col_frame, text="UNIQUE", variable=self.var_unique).grid(row=0, column=6, padx=(0, 10))

        ttk.Button(add_col_frame, text="Agregar columna", command=self.agregar_columna).grid(row=0, column=7)

        btn_frame = ttk.Frame(table_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Crear tabla", command=self.crear_tabla_avanzada).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Limpiar", command=self.limpiar_columnas).pack(side=tk.LEFT)

    def create_insert_tab(self):
        """Pestaña mejorada para insertar datos"""
        self.tab_insert = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_insert, text="➕ Insertar Datos")

        insert_frame = ttk.LabelFrame(self.tab_insert, text="Inserción de Datos", padding="10")
        insert_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        table_select_frame = ttk.Frame(insert_frame)
        table_select_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(table_select_frame, text="Seleccionar tabla:").pack(side=tk.LEFT)
        self.combo_tabla_insert = ttk.Combobox(table_select_frame, width=20, state="readonly")
        self.combo_tabla_insert.pack(side=tk.LEFT, padx=(10, 0))
        self.combo_tabla_insert.bind('<<ComboboxSelected>>', self.on_tabla_selected)

        ttk.Button(table_select_frame, text="Actualizar", command=self.actualizar_tablas).pack(side=tk.LEFT, padx=(10, 0))

        self.fields_frame = ttk.LabelFrame(insert_frame, text="Campos", padding="5")
        self.fields_frame.pack(fill=tk.X, pady=(0, 10))

        btn_insert_frame = ttk.Frame(insert_frame)
        btn_insert_frame.pack(fill=tk.X)

        ttk.Button(btn_insert_frame, text="Insertar datos", command=self.insertar_datos_mejorado).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_insert_frame, text="Limpiar campos", command=self.limpiar_campos).pack(side=tk.LEFT)

    def create_query_tab(self):
        """Pestaña mejorada para consultas"""
        self.tab_query = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_query, text="🔍 Consultas SQL")

        query_frame = ttk.LabelFrame(self.tab_query, text="Ejecutar Consultas SQL", padding="10")
        query_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        sql_frame = ttk.LabelFrame(query_frame, text="Consulta SQL", padding="5")
        sql_frame.pack(fill=tk.X, pady=(0, 10))

        self.text_consulta = scrolledtext.ScrolledText(sql_frame, height=6, width=70)
        self.text_consulta.pack(fill=tk.X, pady=(0, 10))

        btn_query_frame = ttk.Frame(sql_frame)
        btn_query_frame.pack(fill=tk.X)

        ttk.Button(btn_query_frame, text="Ejecutar consulta", command=self.ejecutar_consulta).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_query_frame, text="Limpiar", command=lambda: self.text_consulta.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_query_frame, text="Consultas de ejemplo", command=self.mostrar_ejemplos).pack(side=tk.LEFT)

        results_frame = ttk.LabelFrame(query_frame, text="Resultados", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_results = ttk.Treeview(results_frame)
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree_results.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.tree_results.xview)

        self.tree_results.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.tree_results.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

    def create_view_tab(self):
        """Pestaña mejorada para ver estructura de BD"""
        self.tab_view = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_view, text="📊 Estructura BD")

        view_frame = ttk.LabelFrame(self.tab_view, text="Estructura de la Base de Datos", padding="10")
        view_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_view_frame = ttk.Frame(view_frame)
        btn_view_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_view_frame, text="Actualizar estructura", command=self.actualizar_estructura).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_view_frame, text="Exportar esquema", command=self.exportar_esquema).pack(side=tk.LEFT)

        self.text_estructura = scrolledtext.ScrolledText(view_frame, height=25, width=80)
        self.text_estructura.pack(fill=tk.BOTH, expand=True)

    def create_export_tab(self):
        """Nueva pestaña para exportar datos"""
        self.tab_export = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_export, text="💾 Exportar")

        export_frame = ttk.LabelFrame(self.tab_export, text="Exportar Datos", padding="10")
        export_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        table_frame = ttk.Frame(export_frame)
        table_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(table_frame, text="Seleccionar tabla:").pack(side=tk.LEFT)
        self.combo_tabla_export = ttk.Combobox(table_frame, width=20, state="readonly")
        self.combo_tabla_export.pack(side=tk.LEFT, padx=(10, 0))

        formato_frame = ttk.LabelFrame(export_frame, text="Formato", padding="5")
        formato_frame.pack(fill=tk.X, pady=(0, 10))

        self.var_formato = tk.StringVar(value="csv")
        ttk.Radiobutton(formato_frame, text="CSV", variable=self.var_formato, value="csv").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(formato_frame, text="Excel", variable=self.var_formato, value="excel").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(formato_frame, text="SQL", variable=self.var_formato, value="sql").pack(side=tk.LEFT)

        btn_export_frame = ttk.Frame(export_frame)
        btn_export_frame.pack(fill=tk.X)

        ttk.Button(btn_export_frame, text="Exportar tabla", command=self.exportar_tabla).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_export_frame, text="Backup completo", command=self.backup_completo).pack(side=tk.LEFT)

    def mostrar_ejemplos(self):
        """Mostrar ventana con consultas de ejemplo"""
        ejemplos_window = tk.Toplevel(self.root)
        ejemplos_window.title("Consultas SQL de Ejemplo")
        ejemplos_window.geometry("600x500")

        frame = ttk.Frame(ejemplos_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Consultas SQL de Ejemplo", font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        ejemplos_text = scrolledtext.ScrolledText(frame, height=25, width=70)
        ejemplos_text.pack(fill=tk.BOTH, expand=True)

        ejemplos = """
-- CONSULTAS BÁSICAS --

-- Seleccionar todos los registros
SELECT * FROM datos;

-- Seleccionar columnas específicas
SELECT nombre, edad FROM datos;

-- Filtrar con WHERE
SELECT * FROM datos WHERE edad > 25;

-- Ordenar resultados
SELECT * FROM datos ORDER BY edad DESC;

-- Contar registros
SELECT COUNT(*) FROM datos;

-- Agrupar y contar
SELECT edad, COUNT(*) as cantidad FROM datos GROUP BY edad;

-- CONSULTAS INTERMEDIAS --

-- Filtros múltiples
SELECT * FROM datos WHERE edad BETWEEN 20 AND 40 AND nombre LIKE 'A%';

-- Subconsultas
SELECT * FROM datos WHERE edad > (SELECT AVG(edad) FROM datos);

-- Unir tablas (si tienes múltiples tablas)
SELECT d.nombre, d.edad FROM datos d 
INNER JOIN otra_tabla o ON d.id = o.dato_id;

-- CONSULTAS DE MODIFICACIÓN --

-- Actualizar registros
UPDATE datos SET edad = 30 WHERE nombre = 'Juan';

-- Eliminar registros
DELETE FROM datos WHERE edad < 18;

-- CONSULTAS DE ESTRUCTURA --

-- Ver estructura de tabla
PRAGMA table_info(datos);

-- Listar todas las tablas
SELECT name FROM sqlite_master WHERE type='table';

-- Ver índices
SELECT name FROM sqlite_master WHERE type='index';
        """

        ejemplos_text.insert(1.0, ejemplos)
        ejemplos_text.config(state=tk.DISABLED)

        ttk.Button(frame, text="Cerrar", command=ejemplos_window.destroy).pack(pady=10)

    def actualizar_estructura(self):
        """Actualizar información de estructura de BD"""
        self.text_estructura.delete(1.0, tk.END)

        try:
            self.text_estructura.insert(tk.END, "=== ESTRUCTURA DE LA BASE DE DATOS ===\n\n")
            self.text_estructura.insert(tk.END, f"Archivo: {self.db_path}\n")
            self.text_estructura.insert(tk.END, f"Fecha de actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas = self.cursor.fetchall()

            if not tablas:
                self.text_estructura.insert(tk.END, "No hay tablas en la base de datos.\n")
                return

            self.text_estructura.insert(tk.END, f"Número de tablas: {len(tablas)}\n\n")

            for i, (tabla,) in enumerate(tablas, 1):
                self.text_estructura.insert(tk.END, f"{i}. TABLA: {tabla}\n")
                self.text_estructura.insert(tk.END, "=" * (len(tabla) + 10) + "\n")

                self.cursor.execute(f"PRAGMA table_info({tabla})")
                columnas = self.cursor.fetchall()

                self.text_estructura.insert(tk.END, "Columnas:\n")
                for col in columnas:
                    col_id, nombre, tipo, not_null, default, pk = col
                    pk_text = " (PRIMARY KEY)" if pk else ""
                    null_text = " NOT NULL" if not_null else ""
                    default_text = f" DEFAULT {default}" if default else ""
                    self.text_estructura.insert(
                        tk.END,
                        f"  - {nombre}: {tipo}{null_text}{default_text}{pk_text}\n"
                    )

                self.cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = self.cursor.fetchone()[0]
                self.text_estructura.insert(tk.END, f"Número de registros: {count}\n")

                self.cursor.execute(f"PRAGMA index_list({tabla})")
                indices = self.cursor.fetchall()
                if indices:
                    self.text_estructura.insert(tk.END, "Índices:\n")
                    for idx in indices:
                        self.text_estructura.insert(
                            tk.END,
                            f"  - {idx[1]} (único: {'sí' if idx[2] else 'no'})\n"
                        )

                self.text_estructura.insert(tk.END, "\n" + "-" * 50 + "\n\n")

            self.update_status("Estructura actualizada")

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener estructura:\n{str(e)}")

    def exportar_esquema(self):
        """Exportar esquema SQL de la base de datos"""
        try:
            archivo = filedialog.asksaveasfilename(
                title="Guardar esquema SQL",
                defaultextension=".sql",
                filetypes=[("Archivos SQL", "*.sql"), ("Todos los archivos", "*.*")]
            )

            if archivo:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write("-- Esquema de base de datos\n")
                    f.write(f"-- Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
                    schemas = self.cursor.fetchall()

                    for schema in schemas:
                        f.write(schema[0] + ";\n\n")

                messagebox.showinfo("Éxito", f"Esquema exportado a: {archivo}")
                self.update_status("Esquema exportado")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar esquema:\n{str(e)}")

    def exportar_tabla(self):
        """Exportar tabla seleccionada"""
        tabla = self.combo_tabla_export.get()
        if not tabla:
            messagebox.showwarning("Advertencia", "Seleccione una tabla")
            return

        formato = self.var_formato.get()

        try:
            if formato == "csv":
                archivo = filedialog.asksaveasfilename(
                    title=f"Exportar tabla {tabla} como CSV",
                    defaultextension=".csv",
                    filetypes=[("Archivos CSV", "*.csv")]
                )
                if archivo:
                    df = pd.read_sql_query(f"SELECT * FROM {tabla}", self.conexion)
                    df.to_csv(archivo, index=False)

            elif formato == "excel":
                archivo = filedialog.asksaveasfilename(
                    title=f"Exportar tabla {tabla} como Excel",
                    defaultextension=".xlsx",
                    filetypes=[("Archivos Excel", "*.xlsx")]
                )
                if archivo:
                    df = pd.read_sql_query(f"SELECT * FROM {tabla}", self.conexion)
                    df.to_excel(archivo, index=False)

            elif formato == "sql":
                archivo = filedialog.asksaveasfilename(
                    title=f"Exportar tabla {tabla} como SQL",
                    defaultextension=".sql",
                    filetypes=[("Archivos SQL", "*.sql")]
                )
                if archivo:
                    with open(archivo, 'w', encoding='utf-8') as f:
                        self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{tabla}'")
                        schema = self.cursor.fetchone()[0]
                        f.write(f"{schema};\n\n")

                        self.cursor.execute(f"SELECT * FROM {tabla}")
                        rows = self.cursor.fetchall()

                        self.cursor.execute(f"PRAGMA table_info({tabla})")
                        cols = [col[1] for col in self.cursor.fetchall()]

                        for row in rows:
                            values = ", ".join(
                                [f"'{str(v)}'" if v is not None else "NULL" for v in row]
                            )
                            f.write(f"INSERT INTO {tabla} ({', '.join(cols)}) VALUES ({values});\n")

            if archivo:
                messagebox.showinfo("Éxito", f"Tabla exportada exitosamente")
                self.update_status(f"Tabla '{tabla}' exportada")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar:\n{str(e)}")

    def backup_completo(self):
        """Crear backup completo de la base de datos"""
        try:
            archivo = filedialog.asksaveasfilename(
                title="Guardar backup completo",
                defaultextension=".sql",
                filetypes=[("Archivos SQL", "*.sql")]
            )

            if archivo:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write("-- Backup completo de base de datos\n")
                    f.write(f"-- Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    for line in self.conexion.iterdump():
                        f.write(f"{line}\n")

                messagebox.showinfo("Éxito", "Backup completo creado exitosamente")
                self.update_status("Backup completo realizado")

        except Exception as e:
            messagebox.showerror("Error", f"Error al crear backup:\n{str(e)}")

    def update_status(self, mensaje):
        """Actualizar barra de estado"""
        self.status_var.set(f"{datetime.now().strftime('%H:%M:%S')} - {mensaje}")

    def cargar_csv(self):
        """Cargar y previsualizar archivo CSV"""
        archivo_csv = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )

        if archivo_csv:
            try:
                self.current_csv_data = pd.read_csv(archivo_csv, encoding='utf-8')
                self.label_csv.config(text=f"Archivo: {os.path.basename(archivo_csv)}", foreground="green")
                self.btn_procesar_csv.config(state=tk.NORMAL)
                self.mostrar_preview_csv()
                self.update_status(f"CSV cargado: {len(self.current_csv_data)} filas, {len(self.current_csv_data.columns)} columnas")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo CSV:\n{str(e)}")
                self.current_csv_data = None
                self.btn_procesar_csv.config(state=tk.DISABLED)

    def mostrar_preview_csv(self):
        """Mostrar vista previa del CSV en el Treeview"""
        for item in self.tree_csv.get_children():
            self.tree_csv.delete(item)

        if self.current_csv_data is not None:
            self.tree_csv["columns"] = list(self.current_csv_data.columns)
            self.tree_csv["show"] = "headings"

            for col in self.current_csv_data.columns:
                self.tree_csv.heading(col, text=col)
                self.tree_csv.column(col, width=100)

            for _, row in self.current_csv_data.head(100).iterrows():
                self.tree_csv.insert("", "end", values=list(row))

    def procesar_csv(self):
        """Procesar CSV y cargar a la base de datos"""
        if self.current_csv_data is None:
            messagebox.showwarning("Advertencia", "No hay datos CSV cargados")
            return

        tabla_nombre = self.entry_tabla_csv.get().strip()
        if not tabla_nombre:
            messagebox.showwarning("Advertencia", "Ingrese un nombre para la tabla")
            return

        try:
            if_exists = "replace" if self.var_replace.get() else "fail"
            self.current_csv_data.to_sql(tabla_nombre, self.conexion, if_exists=if_exists, index=False)
            messagebox.showinfo("Éxito", f"Datos cargados exitosamente en la tabla '{tabla_nombre}'")
            self.update_status(f"Tabla '{tabla_nombre}' creada con {len(self.current_csv_data)} registros")
            self.actualizar_tablas()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos:\n{str(e)}")

    def agregar_columna(self):
        """Agregar columna a la lista"""
        nombre = self.entry_col_nombre.get().strip()
        tipo = self.combo_tipo.get()

        if not nombre:
            messagebox.showwarning("Advertencia", "Ingrese un nombre para la columna")
            return

        restricciones = []
        if self.var_primary.get():
            restricciones.append("PRIMARY KEY")
        if self.var_not_null.get():
            restricciones.append("NOT NULL")
        if self.var_unique.get():
            restricciones.append("UNIQUE")

        restricciones_str = ", ".join(restricciones)
        self.tree_columns.insert("", "end", values=(nombre, tipo, restricciones_str))

        self.entry_col_nombre.delete(0, tk.END)
        self.var_primary.set(False)
        self.var_not_null.set(False)
        self.var_unique.set(False)

    def crear_tabla_avanzada(self):
        """Crear tabla con columnas definidas"""
        nombre_tabla = self.entry_tabla_nombre.get().strip()
        if not nombre_tabla:
            messagebox.showwarning("Advertencia", "Ingrese un nombre para la tabla")
            return

        columnas = []
        for item in self.tree_columns.get_children():
            values = self.tree_columns.item(item)["values"]
            col_def = f"{values[0]} {values[1]} {values[2]}".strip()
            columnas.append(col_def)

        if not columnas:
            messagebox.showwarning("Advertencia", "Agregue al menos una columna")
            return

        try:
            sql = f"CREATE TABLE IF NOT EXISTS {nombre_tabla} ({', '.join(columnas)})"
            self.cursor.execute(sql)
            self.conexion.commit()

            messagebox.showinfo("Éxito", f"Tabla '{nombre_tabla}' creada exitosamente")
            self.update_status(f"Tabla '{nombre_tabla}' creada")
            self.entry_tabla_nombre.delete(0, tk.END)
            self.limpiar_columnas()
            self.actualizar_tablas()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al crear tabla:\n{str(e)}")

    def limpiar_columnas(self):
        """Limpiar lista de columnas"""
        for item in self.tree_columns.get_children():
            self.tree_columns.delete(item)

    def actualizar_tablas(self):
        """Actualizar lista de tablas en combos"""
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas = [row[0] for row in self.cursor.fetchall()]
            self.combo_tabla_insert['values'] = tablas
            self.combo_tabla_export['values'] = tablas
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener tablas:\n{str(e)}")

    def on_tabla_selected(self, event):
        """Cuando se selecciona una tabla, mostrar sus campos"""
        tabla = self.combo_tabla_insert.get()
        if not tabla:
            return

        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        self.field_entries.clear()

        try:
            self.cursor.execute(f"PRAGMA table_info({tabla})")
            columnas = self.cursor.fetchall()

            for i, col in enumerate(columnas):
                col_name = col[1]
                col_type = col[2]
                is_pk = col[5]

                ttk.Label(self.fields_frame, text=f"{col_name} ({col_type}):").grid(
                    row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2
                )
                entry = ttk.Entry(self.fields_frame, width=30)
                entry.grid(row=i, column=1, sticky=tk.W, pady=2)

                if is_pk:
                    entry.insert(0, "AUTO")
                    entry.config(state="readonly")

                self.field_entries[col_name] = entry

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener estructura de tabla:\n{str(e)}")

    def insertar_datos_mejorado(self):
        """Insertar datos usando los campos dinámicos"""
        tabla = self.combo_tabla_insert.get()
        if not tabla:
            messagebox.showwarning("Advertencia", "Seleccione una tabla")
            return

        valores = {}
        for campo, entry in self.field_entries.items():
            valor = entry.get().strip()
            if valor and valor != "AUTO":
                valores[campo] = valor

        if not valores:
            messagebox.showwarning("Advertencia", "Ingrese al menos un valor")
            return

        try:
            columnas = ", ".join(valores.keys())
            placeholders = ", ".join(["?" for _ in valores])
            sql = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"

            self.cursor.execute(sql, list(valores.values()))
            self.conexion.commit()

            messagebox.showinfo("Éxito", "Datos insertados correctamente")
            self.update_status(f"Registro insertado en tabla '{tabla}'")
            self.limpiar_campos()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al insertar datos:\n{str(e)}")

    def limpiar_campos(self):
        """Limpiar campos de inserción"""
        for entry in self.field_entries.values():
            if entry['state'] != 'readonly':
                entry.delete(0, tk.END)

    def ejecutar_consulta(self):
        """Ejecutar consulta SQL mejorada"""
        consulta = self.text_consulta.get(1.0, tk.END).strip()
        if not consulta:
            messagebox.showwarning("Advertencia", "Ingrese una consulta SQL")
            return

        try:
            for item in self.tree_results.get_children():
                self.tree_results.delete(item)

            self.cursor.execute(consulta)
            resultados = self.cursor.fetchall()

            if resultados:
                columnas = [description[0] for description in self.cursor.description]
                self.tree_results["columns"] = columnas
                self.tree_results["show"] = "headings"

                for col in columnas:
                    self.tree_results.heading(col, text=col)
                    self.tree_results.column(col, width=120)

                for fila in resultados:
                    self.tree_results.insert("", "end", values=fila)

                self.update_status(f"Consulta ejecutada: {len(resultados)} registros encontrados")
            else:
                self.tree_results["columns"] = ()
                self.tree_results["show"] = "tree"
                self.update_status("Consulta ejecutada: sin resultados")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error en la consulta:\n{str(e)}")
            self.update_status("Error en consulta SQL")

    def insertar_datos(self):
        """Método de compatibilidad con versión anterior"""
        nombre = getattr(self, 'entry_nombre', None)
        edad = getattr(self, 'entry_edad', None)
        if nombre and edad:
            try:
                self.cursor.execute("INSERT INTO datos (nombre, edad) VALUES (?, ?)", (nombre.get(), edad.get()))
                self.conexion.commit()
                messagebox.showinfo("Datos insertados", "Los datos han sido insertados")
                self.update_status("Datos insertados en tabla 'datos'")
            except sqlite3.OperationalError:
                messagebox.showerror("Error", "La tabla 'datos' no existe")

    def consultar_datos(self):
        """Método de compatibilidad con versión anterior"""
        consulta_widget = getattr(self, 'entry_consulta', None)
        if consulta_widget:
            consulta = consulta_widget.get()
            try:
                self.cursor.execute(consulta)
                resultados = self.cursor.fetchall()
                resultados_widget = getattr(self, 'text_resultados', None)
                if resultados_widget:
                    resultados_widget.delete(1.0, tk.END)
                    for resultado in resultados:
                        resultados_widget.insert(tk.END, str(resultado) + "\n")
            except sqlite3.Error as e:
                messagebox.showerror("Error", str(e))

    def crear_tabla(self):
        """Método de compatibilidad con versión anterior"""
        entry_tabla_widget = getattr(self, 'entry_tabla', None)
        if entry_tabla_widget:
            nombre_tabla = entry_tabla_widget.get()
            try:
                self.cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {nombre_tabla} "
                    f"(id INTEGER PRIMARY KEY, nombre TEXT, edad INTEGER)"
                )
                self.conexion.commit()
                messagebox.showinfo("Tabla creada", f"La tabla {nombre_tabla} ha sido creada")
                self.update_status(f"Tabla '{nombre_tabla}' creada")
            except sqlite3.Error as e:
                messagebox.showerror("Error", str(e))

    def ver_tablas(self):
        """Método de compatibilidad - redirige a actualizar estructura"""
        self.notebook.select(4)  # Seleccionar pestaña de estructura
        self.actualizar_estructura()

    def on_closing(self):
        """Manejar cierre de la aplicación"""
        try:
            if self.conexion:
                self.conexion.close()
        except:
            pass
        finally:
            self.root.destroy()

def main():
    """Función principal con manejo de errores"""
    try:
        root = tk.Tk()
        try:
            root.iconbitmap('sql_icon.ico')  # Opcional
        except:
            pass

        app = SQLApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error crítico", f"Error al iniciar la aplicación:\n{str(e)}")

if __name__ == "__main__":
    main()
