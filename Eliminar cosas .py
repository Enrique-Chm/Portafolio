import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import winreg
import os
import sys
import threading
import shutil
import glob
from datetime import datetime
import json

class SafeUninstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Desinstalador Completo y Seguro")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Lista para almacenar programas
        self.programs = []
        self.selected_programs = []
        self.residual_files = {}
        
        # Crear carpeta de respaldos
        self.backup_folder = os.path.join(os.path.expanduser("~"), "Desktop", "Respaldos_Desinstalacion")
        
        self.create_widgets()
        self.load_programs()
        
    def create_widgets(self):
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña principal de desinstalación
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Desinstalar Programas")
        
        # Pestaña de limpieza de archivos residuales
        self.cleanup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.cleanup_tab, text="Limpiar Archivos Residuales")
        
        self.create_main_tab()
        self.create_cleanup_tab()
        
    def create_main_tab(self):
        """Crea la pestaña principal de desinstalación"""
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Desinstalador Completo y Seguro", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Frame de búsqueda
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(search_frame, text="Buscar:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_programs)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        refresh_btn = ttk.Button(search_frame, text="Actualizar Lista", command=self.refresh_programs)
        refresh_btn.pack(side='right')
        
        # Frame principal con lista y botones
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Lista de programas
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Treeview para mostrar programas
        columns = ('Nombre', 'Editor', 'Versión', 'Tamaño')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.tree.heading('Nombre', text='Nombre del Programa')
        self.tree.heading('Editor', text='Editor')
        self.tree.heading('Versión', text='Versión')
        self.tree.heading('Tamaño', text='Tamaño')
        
        self.tree.column('Nombre', width=300)
        self.tree.column('Editor', width=150)
        self.tree.column('Versión', width=100)
        self.tree.column('Tamaño', width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid del treeview y scrollbars
        self.tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Frame de botones
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(side='right', fill='y')
        
        # Botones
        ttk.Button(button_frame, text="Seleccionar", command=self.select_program).pack(pady=(0, 5), fill='x')
        ttk.Button(button_frame, text="Deseleccionar", command=self.unselect_program).pack(pady=(0, 5), fill='x')
        ttk.Button(button_frame, text="Ver Detalles", command=self.show_program_info).pack(pady=(0, 10), fill='x')
        ttk.Button(button_frame, text="Analizar Archivos", command=self.analyze_residual_files).pack(pady=(0, 5), fill='x')
        ttk.Button(button_frame, text="Desinstalar + Limpiar", command=self.uninstall_and_cleanup, style='Accent.TButton').pack(pady=(0, 5), fill='x')
        
        # Frame de información
        info_frame = ttk.LabelFrame(main_frame, text="Programas Seleccionados", padding="5")
        info_frame.pack(fill='x', pady=(10, 0))
        
        self.selected_listbox = tk.Listbox(info_frame, height=4)
        self.selected_listbox.pack(side='left', fill='x', expand=True)
        
        selected_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.selected_listbox.yview)
        selected_scroll.pack(side='right', fill='y')
        self.selected_listbox.configure(yscrollcommand=selected_scroll.set)
        
        # Opciones de limpieza
        options_frame = ttk.LabelFrame(main_frame, text="Opciones de Limpieza", padding="5")
        options_frame.pack(fill='x', pady=(10, 0))
        
        self.backup_var = tk.BooleanVar(value=True)
        self.clean_appdata_var = tk.BooleanVar(value=True)
        self.clean_documents_var = tk.BooleanVar(value=False)
        self.clean_temp_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Crear respaldo antes de limpiar", variable=self.backup_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Limpiar configuraciones en AppData", variable=self.clean_appdata_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Limpiar archivos en Documentos (¡CUIDADO!)", variable=self.clean_documents_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Limpiar archivos temporales", variable=self.clean_temp_var).pack(anchor='w')
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill='x', pady=(10, 0))
        
    def create_cleanup_tab(self):
        """Crea la pestaña de limpieza de archivos residuales"""
        cleanup_frame = ttk.Frame(self.cleanup_tab, padding="10")
        cleanup_frame.pack(fill='both', expand=True)
        
        # Título
        title_label = ttk.Label(cleanup_frame, text="Análisis de Archivos Residuales", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Frame de controles
        controls_frame = ttk.Frame(cleanup_frame)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(controls_frame, text="Escanear Archivos Residuales", command=self.scan_residual_files).pack(side='left', padx=(0, 10))
        ttk.Button(controls_frame, text="Seleccionar Todo", command=self.select_all_residual).pack(side='left', padx=(0, 10))
        ttk.Button(controls_frame, text="Deseleccionar Todo", command=self.deselect_all_residual).pack(side='left', padx=(0, 10))
        ttk.Button(controls_frame, text="Limpiar Seleccionados", command=self.clean_selected_residual).pack(side='right')
        
        # Lista de archivos residuales
        residual_frame = ttk.LabelFrame(cleanup_frame, text="Archivos Residuales Encontrados", padding="5")
        residual_frame.pack(fill='both', expand=True)
        
        # Treeview para archivos residuales
        residual_columns = ('Seleccionar', 'Tipo', 'Ubicación', 'Tamaño', 'Programa')
        self.residual_tree = ttk.Treeview(residual_frame, columns=residual_columns, show='headings')
        
        self.residual_tree.heading('Seleccionar', text='☐')
        self.residual_tree.heading('Tipo', text='Tipo')
        self.residual_tree.heading('Ubicación', text='Ubicación')
        self.residual_tree.heading('Tamaño', text='Tamaño')
        self.residual_tree.heading('Programa', text='Programa Relacionado')
        
        self.residual_tree.column('Seleccionar', width=50)
        self.residual_tree.column('Tipo', width=100)
        self.residual_tree.column('Ubicación', width=400)
        self.residual_tree.column('Tamaño', width=80)
        self.residual_tree.column('Programa', width=150)
        
        # Scrollbars para residual tree
        residual_v_scroll = ttk.Scrollbar(residual_frame, orient=tk.VERTICAL, command=self.residual_tree.yview)
        residual_h_scroll = ttk.Scrollbar(residual_frame, orient=tk.HORIZONTAL, command=self.residual_tree.xview)
        self.residual_tree.configure(yscrollcommand=residual_v_scroll.set, xscrollcommand=residual_h_scroll.set)
        
        self.residual_tree.pack(side='left', fill='both', expand=True)
        residual_v_scroll.pack(side='right', fill='y')
        residual_h_scroll.pack(side='bottom', fill='x')
        
        # Evento para seleccionar/deseleccionar archivos
        self.residual_tree.bind('<Button-1>', self.toggle_residual_selection)
        
        # Información de limpieza
        info_text = """
INFORMACIÓN IMPORTANTE:
• Los archivos se respaldarán automáticamente antes de eliminar
• Solo se mostrarán archivos de programas ya desinstalados
• Revisa cuidadosamente antes de limpiar archivos en Documentos
• Los respaldos se guardarán en el Escritorio
        """
        info_label = ttk.Label(cleanup_frame, text=info_text, justify='left', font=('Arial', 9))
        info_label.pack(pady=(10, 0))
        
    def load_programs(self):
        """Carga la lista de programas instalados de forma segura"""
        self.status_var.set("Cargando programas instalados...")
        self.root.update()
        
        self.programs = []
        
        try:
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hkey, path in registry_paths:
                try:
                    registry_key = winreg.OpenKey(hkey, path)
                    for i in range(winreg.QueryInfoKey(registry_key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(registry_key, i)
                            subkey = winreg.OpenKey(registry_key, subkey_name)
                            
                            program_info = self.get_program_info(subkey)
                            if program_info and self.is_safe_to_uninstall(program_info):
                                self.programs.append(program_info)
                                
                            winreg.CloseKey(subkey)
                        except Exception:
                            continue
                    winreg.CloseKey(registry_key)
                except Exception:
                    continue
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar programas: {str(e)}")
        
        self.update_program_list()
        self.status_var.set(f"Se encontraron {len(self.programs)} programas")
        
    def get_program_info(self, registry_key):
        """Extrae información del programa desde el registro"""
        try:
            display_name = winreg.QueryValueEx(registry_key, "DisplayName")[0]
            
            try:
                publisher = winreg.QueryValueEx(registry_key, "Publisher")[0]
            except:
                publisher = "Desconocido"
                
            try:
                version = winreg.QueryValueEx(registry_key, "DisplayVersion")[0]
            except:
                version = "N/A"
                
            try:
                size = winreg.QueryValueEx(registry_key, "EstimatedSize")[0]
                size_mb = f"{size/1024:.1f} MB" if size else "N/A"
            except:
                size_mb = "N/A"
                
            try:
                uninstall_string = winreg.QueryValueEx(registry_key, "UninstallString")[0]
            except:
                uninstall_string = None
                
            try:
                install_location = winreg.QueryValueEx(registry_key, "InstallLocation")[0]
            except:
                install_location = None
                
            return {
                'name': display_name,
                'publisher': publisher,
                'version': version,
                'size': size_mb,
                'uninstall_string': uninstall_string,
                'install_location': install_location
            }
        except:
            return None
            
    def is_safe_to_uninstall(self, program_info):
        """Verifica si es seguro mostrar el programa para desinstalar"""
        if not program_info or not program_info.get('name') or not program_info.get('uninstall_string'):
            return False
            
        name = program_info['name'].lower()
        publisher = program_info.get('publisher', '').lower()
        
        critical_keywords = [
            'microsoft visual c++',
            'microsoft .net',
            '.net framework',
            'windows',
            'driver',
            'directx',
            'system',
            'runtime',
            'redistributable',
            'security update',
            'kb[0-9]',
            'hotfix'
        ]
        
        critical_publishers = [
            'microsoft corporation',
            'intel',
            'nvidia',
            'amd',
            'realtek'
        ]
        
        for keyword in critical_keywords:
            if keyword in name:
                return False
                
        for pub in critical_publishers:
            if pub in publisher:
                return False
                
        return True
        
    def update_program_list(self):
        """Actualiza la lista visual de programas"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_term = self.search_var.get().lower()
        filtered_programs = [p for p in self.programs if search_term in p['name'].lower()]
        
        for program in filtered_programs:
            self.tree.insert('', 'end', values=(
                program['name'],
                program['publisher'],
                program['version'],
                program['size']
            ))
            
    def filter_programs(self, *args):
        """Filtra programas según el término de búsqueda"""
        self.update_program_list()
        
    def refresh_programs(self):
        """Actualiza la lista de programas"""
        self.load_programs()
        
    def select_program(self):
        """Selecciona un programa para desinstalar"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Por favor selecciona un programa")
            return
            
        item = self.tree.item(selection[0])
        program_name = item['values'][0]
        
        selected_program = next((p for p in self.programs if p['name'] == program_name), None)
        if selected_program and selected_program not in self.selected_programs:
            self.selected_programs.append(selected_program)
            self.update_selected_list()
            
    def unselect_program(self):
        """Deselecciona un programa"""
        selection = self.selected_listbox.curselection()
        if selection:
            index = selection[0]
            del self.selected_programs[index]
            self.update_selected_list()
            
    def update_selected_list(self):
        """Actualiza la lista de programas seleccionados"""
        self.selected_listbox.delete(0, tk.END)
        for program in self.selected_programs:
            self.selected_listbox.insert(tk.END, program['name'])
            
    def show_program_info(self):
        """Muestra información detallada del programa"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Por favor selecciona un programa")
            return
            
        item = self.tree.item(selection[0])
        program_name = item['values'][0]
        
        program = next((p for p in self.programs if p['name'] == program_name), None)
        if program:
            info = f"""Nombre: {program['name']}
Editor: {program['publisher']}
Versión: {program['version']}
Tamaño: {program['size']}
Ubicación: {program.get('install_location', 'No especificada')}
Comando de desinstalación: {program['uninstall_string']}"""
            messagebox.showinfo("Información del Programa", info)
            
    def analyze_residual_files(self):
        """Analiza archivos residuales para los programas seleccionados"""
        if not self.selected_programs:
            messagebox.showwarning("Advertencia", "No hay programas seleccionados")
            return
            
        self.status_var.set("Analizando archivos residuales...")
        self.root.update()
        
        for program in self.selected_programs:
            self.find_residual_files(program)
            
        self.status_var.set("Análisis completado")
        messagebox.showinfo("Análisis", f"Se encontraron archivos residuales para {len(self.residual_files)} programas")
        
    def find_residual_files(self, program):
        """Encuentra archivos residuales de un programa"""
        program_name = program['name']
        residual_locations = []
        
        # Buscar en AppData
        appdata_paths = [
            os.path.join(os.path.expanduser("~"), "AppData", "Local"),
            os.path.join(os.path.expanduser("~"), "AppData", "Roaming"),
            os.path.join(os.path.expanduser("~"), "AppData", "LocalLow")
        ]
        
        for appdata_path in appdata_paths:
            if os.path.exists(appdata_path):
                for item in os.listdir(appdata_path):
                    if self.is_related_to_program(item, program_name):
                        full_path = os.path.join(appdata_path, item)
                        if os.path.isdir(full_path):
                            size = self.get_folder_size(full_path)
                            residual_locations.append({
                                'type': 'Configuración',
                                'path': full_path,
                                'size': size,
                                'program': program_name
                            })
        
        # Buscar en Documentos (opcional)
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        if os.path.exists(documents_path):
            for item in os.listdir(documents_path):
                if self.is_related_to_program(item, program_name):
                    full_path = os.path.join(documents_path, item)
                    if os.path.isdir(full_path):
                        size = self.get_folder_size(full_path)
                        residual_locations.append({
                            'type': 'Documentos',
                            'path': full_path,
                            'size': size,
                            'program': program_name
                        })
        
        # Buscar archivos temporales
        temp_paths = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
        ]
        
        for temp_path in temp_paths:
            if temp_path and os.path.exists(temp_path):
                try:
                    for item in os.listdir(temp_path):
                        if self.is_related_to_program(item, program_name):
                            full_path = os.path.join(temp_path, item)
                            size = self.get_path_size(full_path)
                            residual_locations.append({
                                'type': 'Temporal',
                                'path': full_path,
                                'size': size,
                                'program': program_name
                            })
                except:
                    continue
        
        if residual_locations:
            self.residual_files[program_name] = residual_locations
            
    def is_related_to_program(self, folder_name, program_name):
        """Verifica si una carpeta está relacionada con el programa"""
        folder_lower = folder_name.lower()
        program_lower = program_name.lower()
        
        # Extraer palabras clave del nombre del programa
        program_words = program_lower.replace('-', ' ').replace('_', ' ').split()
        program_words = [word for word in program_words if len(word) > 3]  # Ignorar palabras muy cortas
        
        # Verificar si alguna palabra clave está en el nombre de la carpeta
        for word in program_words:
            if word in folder_lower:
                return True
                
        return False
        
    def get_folder_size(self, folder_path):
        """Calcula el tamaño de una carpeta"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        continue
        except:
            pass
        return self.format_size(total_size)
        
    def get_path_size(self, path):
        """Calcula el tamaño de un archivo o carpeta"""
        try:
            if os.path.isfile(path):
                return self.format_size(os.path.getsize(path))
            elif os.path.isdir(path):
                return self.get_folder_size(path)
        except:
            pass
        return "0 B"
        
    def format_size(self, size_bytes):
        """Formatea el tamaño en bytes a una forma legible"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
        
    def scan_residual_files(self):
        """Escanea todo el sistema en busca de archivos residuales"""
        self.status_var.set("Escaneando archivos residuales...")
        self.root.update()
        
        # Limpiar resultados anteriores
        for item in self.residual_tree.get_children():
            self.residual_tree.delete(item)
            
        # Obtener lista de programas instalados para comparar
        installed_programs = [p['name'].lower() for p in self.programs]
        
        # Buscar archivos residuales
        self.scan_appdata_residuals(installed_programs)
        self.scan_documents_residuals(installed_programs)
        self.scan_temp_residuals()
        
        self.status_var.set("Escaneo completado")
        
    def scan_appdata_residuals(self, installed_programs):
        """Escanea AppData en busca de archivos residuales"""
        appdata_paths = [
            ("AppData\\Local", os.path.join(os.path.expanduser("~"), "AppData", "Local")),
            ("AppData\\Roaming", os.path.join(os.path.expanduser("~"), "AppData", "Roaming")),
            ("AppData\\LocalLow", os.path.join(os.path.expanduser("~"), "AppData", "LocalLow"))
        ]
        
        for location_name, appdata_path in appdata_paths:
            if not os.path.exists(appdata_path):
                continue
                
            try:
                for item in os.listdir(appdata_path):
                    full_path = os.path.join(appdata_path, item)
                    if os.path.isdir(full_path):
                        # Verificar si podría ser un residuo
                        is_residual = True
                        item_lower = item.lower()
                        
                        # Verificar si corresponde a un programa instalado
                        for program in installed_programs:
                            if any(word in item_lower for word in program.split() if len(word) > 3):
                                is_residual = False
                                break
                                
                        if is_residual and not self.is_system_folder(item_lower):
                            size = self.get_folder_size(full_path)
                            self.residual_tree.insert('', 'end', values=(
                                '☐', 'Configuración', full_path, size, 'Desconocido'
                            ))
            except:
                continue
                
    def scan_documents_residuals(self, installed_programs):
        """Escanea Documentos en busca de archivos residuales"""
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.exists(documents_path):
            return
            
        try:
            for item in os.listdir(documents_path):
                full_path = os.path.join(documents_path, item)
                if os.path.isdir(full_path):
                    item_lower = item.lower()
                    
                    # Buscar carpetas que podrían ser de programas desinstalados
                    if any(keyword in item_lower for keyword in ['games', 'software', 'app', 'program']):
                        is_residual = True
                        for program in installed_programs:
                            if any(word in item_lower for word in program.split() if len(word) > 3):
                                is_residual = False
                                break
                                
                        if is_residual:
                            size = self.get_folder_size(full_path)
                            self.residual_tree.insert('', 'end', values=(
                                '☐', 'Documentos', full_path, size, 'Posible residuo'
                            ))
        except:
            pass
            
    def scan_temp_residuals(self):
        """Escanea archivos temporales"""
        temp_paths = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
        ]
        
        for temp_path in temp_paths:
            if not temp_path or not os.path.exists(temp_path):
                continue
                
            try:
                for item in os.listdir(temp_path):
                    full_path = os.path.join(temp_path, item)
                    # Solo mostrar archivos/carpetas grandes o con nombres sospechosos
                    size_bytes = 0
                    try:
                        if os.path.isfile(full_path):
                            size_bytes = os.path.getsize(full_path)
                        elif os.path.isdir(full_path):
                            for root, dirs, files in os.walk(full_path):
                                for file in files:
                                    try:
                                        size_bytes += os.path.getsize(os.path.join(root, file))
                                    except:
                                        continue
                    except:
                        continue
                        
                    # Solo mostrar si es mayor a 1MB
                    if size_bytes > 1024 * 1024:
                        size = self.format_size(size_bytes)
                        self.residual_tree.insert('', 'end', values=(
                            '☐', 'Temporal', full_path, size, 'Archivo temporal'
                        ))
            except:
                continue
                
    def is_system_folder(self, folder_name):
        """Verifica si una carpeta es del sistema y no debe ser eliminada"""
        system_folders = [
            'microsoft', 'windows', 'system', 'temp', 'cache', 'history',
            'cookies', 'thumbnails', 'google', 'mozilla', 'adobe',
            'intel', 'nvidia', 'amd', 'realtek', 'programs'
        ]
        return any(sys_folder in folder_name for sys_folder in system_folders)
        
    def toggle_residual_selection(self, event):
        """Cambia el estado de selección de un archivo residual"""
        item = self.residual_tree.selection()[0] if self.residual_tree.selection() else None
        if item:
            current_values = list(self.residual_tree.item(item, 'values'))
            if current_values[0] == '☐':
                current_values[0] = '☑'
            else:
                current_values[0] = '☐'
            self.residual_tree.item(item, values=current_values)
            
    def select_all_residual(self):
        """Selecciona todos los archivos residuales"""
        for item in self.residual_tree.get_children():
            current_values = list(self.residual_tree.item(item, 'values'))
            current_values[0] = '☑'
            self.residual_tree.item(item, values=current_values)
            
    def deselect_all_residual(self):
        """Deselecciona todos los archivos residuales"""
        for item in self.residual_tree.get_children():
            current_values = list(self.residual_tree.item(item, 'values'))
            current_values[0] = '☐'
            self.residual_tree.item(item, values=current_values)
            
    def clean_selected_residual(self):
        """Limpia los archivos residuales seleccionados"""
        selected_files = []
        for item in self.residual_tree.get_children():
            values = self.residual_tree.item(item, 'values')
            if values[0] == '☑':
                selected_files.append(values[2])  # La ruta está en el índice 2
                
        if not selected_files:
            messagebox.showwarning("Advertencia", "No hay archivos seleccionados")
            return
            
        # Confirmar limpieza
        confirm = messagebox.askyesno(
            "Confirmar Limpieza",
            f"¿Estás seguro de que quieres eliminar {len(selected_files)} elementos?\n\n"
            "Se creará un respaldo antes de eliminar."
        )
        
        if confirm:
            threading.Thread(target=self.perform_cleanup, args=(selected_files,), daemon=True).start()
            
    def uninstall_and_cleanup(self):
        """Desinstala programas y limpia archivos residuales"""
        if not self.selected_programs:
            messagebox.showwarning("Advertencia", "No hay programas seleccionados")
            return
            
        # Confirmar desinstalación completa
        program_list = "\n".join([p['name'] for p in self.selected_programs])
        confirm = messagebox.askyesno(
            "Confirmar Desinstalación Completa",
            f"Se realizará:\n\n"
            f"1. Desinstalación de programas:\n{program_list}\n\n"
            f"2. Limpieza de archivos residuales según opciones seleccionadas\n\n"
            f"¿Continuar? (Se crearán respaldos automáticamente)"
        )
        
        if confirm:
            threading.Thread(target=self.perform_complete_uninstall, daemon=True).start()
            
    def perform_complete_uninstall(self):
        """Ejecuta desinstalación completa con limpieza"""
        success_count = 0
        failed_programs = []
        
        # Paso 1: Desinstalar programas
        for i, program in enumerate(self.selected_programs):
            self.status_var.set(f"Desinstalando {program['name']} ({i+1}/{len(self.selected_programs)})")
            self.root.update()
            
            try:
                uninstall_cmd = program['uninstall_string']
                
                if 'msiexec' in uninstall_cmd.lower():
                    if '/I{' in uninstall_cmd:
                        uninstall_cmd = uninstall_cmd.replace('/I{', '/X{')
                    uninstall_cmd += ' /quiet /norestart'
                
                result = subprocess.run(uninstall_cmd, shell=True, capture_output=True, timeout=300)
                
                if result.returncode == 0:
                    success_count += 1
                else:
                    failed_programs.append(program['name'])
                    
            except subprocess.TimeoutExpired:
                failed_programs.append(f"{program['name']} (Tiempo agotado)")
            except Exception as e:
                failed_programs.append(f"{program['name']} (Error: {str(e)})")
        
        # Paso 2: Limpiar archivos residuales
        self.status_var.set("Limpiando archivos residuales...")
        self.root.update()
        
        cleaned_files = []
        for program in self.selected_programs:
            program_cleaned = self.cleanup_program_residuals(program)
            cleaned_files.extend(program_cleaned)
            
        # Mostrar resultados
        self.root.after(0, lambda: self.show_complete_results(success_count, failed_programs, cleaned_files))
        
    def cleanup_program_residuals(self, program):
        """Limpia archivos residuales de un programa específico"""
        cleaned_files = []
        program_name = program['name']
        
        # Crear respaldo si está habilitado
        if self.backup_var.get():
            backup_dir = self.create_backup_folder(program_name)
        else:
            backup_dir = None
            
        # Limpiar AppData
        if self.clean_appdata_var.get():
            appdata_cleaned = self.clean_appdata_files(program_name, backup_dir)
            cleaned_files.extend(appdata_cleaned)
            
        # Limpiar Documentos
        if self.clean_documents_var.get():
            docs_cleaned = self.clean_documents_files(program_name, backup_dir)
            cleaned_files.extend(docs_cleaned)
            
        # Limpiar archivos temporales
        if self.clean_temp_var.get():
            temp_cleaned = self.clean_temp_files(program_name, backup_dir)
            cleaned_files.extend(temp_cleaned)
            
        return cleaned_files
        
    def create_backup_folder(self, program_name):
        """Crea carpeta de respaldo para un programa"""
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in program_name if c.isalnum() or c in (' ', '-', '_'))
            backup_dir = os.path.join(self.backup_folder, f"{safe_name}_{timestamp}")
            os.makedirs(backup_dir)
            return backup_dir
        except:
            return None
            
    def clean_appdata_files(self, program_name, backup_dir):
        """Limpia archivos en AppData"""
        cleaned_files = []
        appdata_paths = [
            os.path.join(os.path.expanduser("~"), "AppData", "Local"),
            os.path.join(os.path.expanduser("~"), "AppData", "Roaming"),
            os.path.join(os.path.expanduser("~"), "AppData", "LocalLow")
        ]
        
        for appdata_path in appdata_paths:
            if not os.path.exists(appdata_path):
                continue
                
            try:
                for item in os.listdir(appdata_path):
                    if self.is_related_to_program(item, program_name):
                        full_path = os.path.join(appdata_path, item)
                        if os.path.exists(full_path):
                            # Crear respaldo
                            if backup_dir:
                                backup_path = os.path.join(backup_dir, "AppData", item)
                                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                                if os.path.isdir(full_path):
                                    shutil.copytree(full_path, backup_path)
                                else:
                                    shutil.copy2(full_path, backup_path)
                                    
                            # Eliminar archivo/carpeta
                            if os.path.isdir(full_path):
                                shutil.rmtree(full_path)
                            else:
                                os.remove(full_path)
                            cleaned_files.append(full_path)
            except Exception as e:
                continue
                
        return cleaned_files
        
    def clean_documents_files(self, program_name, backup_dir):
        """Limpia archivos en Documentos"""
        cleaned_files = []
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        
        if not os.path.exists(documents_path):
            return cleaned_files
            
        try:
            for item in os.listdir(documents_path):
                if self.is_related_to_program(item, program_name):
                    full_path = os.path.join(documents_path, item)
                    if os.path.exists(full_path) and os.path.isdir(full_path):
                        # Crear respaldo
                        if backup_dir:
                            backup_path = os.path.join(backup_dir, "Documents", item)
                            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                            shutil.copytree(full_path, backup_path)
                            
                        # Eliminar carpeta
                        shutil.rmtree(full_path)
                        cleaned_files.append(full_path)
        except Exception as e:
            pass
            
        return cleaned_files
        
    def clean_temp_files(self, program_name, backup_dir):
        """Limpia archivos temporales"""
        cleaned_files = []
        temp_paths = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
        ]
        
        for temp_path in temp_paths:
            if not temp_path or not os.path.exists(temp_path):
                continue
                
            try:
                for item in os.listdir(temp_path):
                    if self.is_related_to_program(item, program_name):
                        full_path = os.path.join(temp_path, item)
                        if os.path.exists(full_path):
                            # Crear respaldo
                            if backup_dir:
                                backup_path = os.path.join(backup_dir, "Temp", item)
                                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                                try:
                                    if os.path.isdir(full_path):
                                        shutil.copytree(full_path, backup_path)
                                    else:
                                        shutil.copy2(full_path, backup_path)
                                except:
                                    pass  # Algunos archivos temp pueden estar en uso
                                    
                            # Eliminar archivo/carpeta
                            try:
                                if os.path.isdir(full_path):
                                    shutil.rmtree(full_path)
                                else:
                                    os.remove(full_path)
                                cleaned_files.append(full_path)
                            except:
                                pass  # Algunos archivos temp pueden estar en uso
            except Exception:
                continue
                
        return cleaned_files
        
    def perform_cleanup(self, selected_files):
        """Ejecuta la limpieza de archivos residuales seleccionados"""
        # Crear respaldo general
        backup_dir = None
        if self.backup_var.get():
            try:
                if not os.path.exists(self.backup_folder):
                    os.makedirs(self.backup_folder)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(self.backup_folder, f"Limpieza_Residuales_{timestamp}")
                os.makedirs(backup_dir)
            except:
                backup_dir = None
                
        cleaned_count = 0
        failed_files = []
        
        for i, file_path in enumerate(selected_files):
            self.status_var.set(f"Limpiando archivo {i+1}/{len(selected_files)}")
            self.root.update()
            
            try:
                if os.path.exists(file_path):
                    # Crear respaldo
                    if backup_dir:
                        rel_path = os.path.relpath(file_path, os.path.commonpath([file_path, backup_dir]))
                        backup_path = os.path.join(backup_dir, rel_path)
                        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                        
                        if os.path.isdir(file_path):
                            shutil.copytree(file_path, backup_path)
                        else:
                            shutil.copy2(file_path, backup_path)
                    
                    # Eliminar archivo/carpeta
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    cleaned_count += 1
                    
            except Exception as e:
                failed_files.append(f"{file_path} (Error: {str(e)})")
                
        # Mostrar resultados
        self.root.after(0, lambda: self.show_cleanup_results(cleaned_count, failed_files, backup_dir))
        
    def show_complete_results(self, success_count, failed_programs, cleaned_files):
        """Muestra los resultados de la desinstalación completa"""
        message = f"Desinstalación completa finalizada.\n\n"
        message += f"Programas desinstalados: {success_count}\n"
        message += f"Archivos residuales limpiados: {len(cleaned_files)}\n"
        
        if failed_programs:
            message += f"\nProgramas que no pudieron desinstalarse:\n"
            message += "\n".join(failed_programs)
            
        if self.backup_var.get():
            message += f"\n\nRespaldos guardados en:\n{self.backup_folder}"
            
        messagebox.showinfo("Desinstalación Completa", message)
        
        # Limpiar y actualizar
        self.selected_programs.clear()
        self.update_selected_list()
        self.refresh_programs()
        self.status_var.set("Listo")
        
    def show_cleanup_results(self, cleaned_count, failed_files, backup_dir):
        """Muestra los resultados de la limpieza"""
        message = f"Limpieza completada.\n\nArchivos eliminados: {cleaned_count}"
        
        if failed_files:
            message += f"\n\nArchivos que no pudieron eliminarse:\n"
            message += "\n".join(failed_files[:10])  # Mostrar solo los primeros 10
            if len(failed_files) > 10:
                message += f"\n... y {len(failed_files) - 10} más"
                
        if backup_dir:
            message += f"\n\nRespaldo guardado en:\n{backup_dir}"
            
        messagebox.showinfo("Limpieza Completada", message)
        self.status_var.set("Listo")
        
        # Actualizar lista de archivos residuales
        self.scan_residual_files()

def main():
    if os.name != 'nt':
        print("Este programa solo funciona en Windows")
        return
        
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("Nota: Para desinstalar algunos programas puede requerirse ejecutar como administrador")
    except:
        pass
        
    root = tk.Tk()
    app = SafeUninstaller(root)
    root.mainloop()

if __name__ == "__main__":
    main()