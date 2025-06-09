import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import threading
import time
from collections import defaultdict

class RAMCleaner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Liberador de RAM Seguro")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Lista blanca de procesos que NO se deben cerrar
        self.protected_processes = {
            # Procesos del sistema críticos
            'system', 'registry', 'smss.exe', 'csrss.exe', 'winlogon.exe', 'services.exe',
            'lsass.exe', 'svchost.exe', 'spoolsv.exe', 'explorer.exe', 'dwm.exe',
            'wininit.exe', 'taskhost.exe', 'taskhostw.exe', 'rundll32.exe',
            
            # Antivirus y seguridad
            'avp.exe', 'avpui.exe', 'kavtray.exe', 'mcshield.exe', 'msmpeng.exe',
            'windefend.exe', 'antimalware service executable', 'windows defender',
            'avgui.exe', 'avguard.exe', 'avcenter.exe', 'norton.exe', 'symantec.exe',
            'bitdefender', 'malwarebytes', 'eset', 'trend micro', 'f-secure',
            
            # Microsoft Office
            'winword.exe', 'excel.exe', 'powerpnt.exe', 'outlook.exe', 'onenote.exe',
            'msaccess.exe', 'publisher.exe', 'visio.exe', 'project.exe', 'teams.exe',
            'skype.exe', 'lync.exe',
            
            # Aplicaciones de comunicación importantes
            'zoom.exe', 'discord.exe', 'slack.exe', 'whatsapp.exe', 'telegram.exe',
            'signal.exe', 'viber.exe',
            
            # Drivers y hardware
            'audiodg.exe', 'nvdisplay.container.exe', 'nvidia web helper.exe',
            'nvidia share.exe', 'rthdvcpl.exe', 'igfxpers.exe', 'igfxtray.exe',
            'amd external events utility.exe', 'radeon software.exe',
            
            # Desarrollo y herramientas importantes
            'python.exe', 'pythonw.exe', 'code.exe', 'devenv.exe', 'xamarin.exe',
            'git.exe', 'node.exe', 'npm.exe', 'docker.exe', 'virtualbox.exe',
            'vmware.exe', 'hyper-v.exe',
            
            # Servicios de Windows importantes
            'wuauclt.exe', 'trustedinstaller.exe', 'msiexec.exe', 'dllhost.exe',
            'conhost.exe', 'fontdrvhost.exe', 'sihost.exe', 'shellexperiencehost.exe',
            'startmenuexperiencehost.exe', 'searchui.exe', 'cortana.exe',
            
            # Backup y almacenamiento en la nube
            'onedrive.exe', 'googledrivesync.exe', 'dropbox.exe', 'boxsync.exe',
            'icloud.exe', 'carbonite.exe', 'crashplan.exe',
            
            # Aplicaciones de productividad comunes
            'notepad.exe', 'notepad++.exe', 'adobe acrobat.exe', 'acrord32.exe',
            'vlc.exe', 'potplayer.exe', '7z.exe', 'winrar.exe', 'winzip.exe'
        }
        
        # Patrones de procesos seguros para cerrar (navegadores, juegos, multimedia)
        self.closeable_patterns = [
            'chrome.exe', 'firefox.exe', 'edge.exe', 'opera.exe', 'brave.exe',
            'iexplore.exe', 'msedge.exe', 'safari.exe', 'vivaldi.exe',
            # Juegos y entretenimiento
            'steam.exe', 'steamwebhelper.exe', 'epicgameslauncher.exe',
            'uplay.exe', 'origin.exe', 'battle.net.exe', 'bethesda.net launcher.exe',
            # Reproductores multimedia no esenciales
            'spotify.exe', 'itunes.exe', 'winamp.exe', 'foobar2000.exe',
            'musicbee.exe', 'mediamonkey.exe', 'aimp.exe'
        ]
        
        self.setup_ui()
        self.update_ram_info()
        
    def setup_ui(self):
        # Marco principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar peso de filas y columnas
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🔧 Liberador de RAM Seguro", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Información de RAM
        ram_frame = ttk.LabelFrame(main_frame, text="Estado de la Memoria RAM", padding="10")
        ram_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        ram_frame.columnconfigure(0, weight=1)
        
        # Etiqueta de uso de RAM
        self.ram_label = ttk.Label(ram_frame, text="Cargando...", font=('Arial', 12))
        self.ram_label.grid(row=0, column=0, pady=(0, 10))
        
        # Barra de progreso de RAM
        self.ram_progress = ttk.Progressbar(ram_frame, length=400, mode='determinate')
        self.ram_progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # TOP 5 procesos
        processes_frame = ttk.LabelFrame(main_frame, text="TOP 5 Procesos que más RAM usan", 
                                       padding="10")
        processes_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        processes_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Tabla de procesos
        columns = ('Proceso', 'RAM (MB)', 'Estado')
        self.processes_tree = ttk.Treeview(processes_frame, columns=columns, show='headings', height=8)
        
        # Configurar columnas
        self.processes_tree.heading('Proceso', text='Proceso')
        self.processes_tree.heading('RAM (MB)', text='RAM (MB)')
        self.processes_tree.heading('Estado', text='Estado')
        
        self.processes_tree.column('Proceso', width=300)
        self.processes_tree.column('RAM (MB)', width=100, anchor='center')
        self.processes_tree.column('Estado', width=100, anchor='center')
        
        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(processes_frame, orient=tk.VERTICAL, command=self.processes_tree.yview)
        self.processes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.processes_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, pady=10)
        
        self.refresh_btn = ttk.Button(buttons_frame, text="🔄 Actualizar", 
                                     command=self.refresh_data)
        self.refresh_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.analyze_btn = ttk.Button(buttons_frame, text="🔍 Analizar liberación de RAM", 
                                     command=self.analyze_ram_liberation)
        self.analyze_btn.grid(row=0, column=1)
        
        # Información adicional
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
        info_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)
        
        info_text = ("ℹ️ Este programa solo sugiere cerrar aplicaciones seguras como navegadores, "
                    "juegos y reproductores multimedia. NUNCA cerrará procesos del sistema, "
                    "antivirus o aplicaciones importantes.")
        info_label = ttk.Label(info_frame, text=info_text, wraplength=750, 
                              justify=tk.LEFT, foreground='blue')
        info_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
    def get_ram_info(self):
        """Obtiene información de la RAM"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent
        }
    
    def get_top_processes(self, limit=5):
        """Obtiene los procesos que más RAM usan"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                process_info = proc.info
                memory_mb = process_info['memory_info'].rss / (1024 * 1024)
                
                # Verificar si es un proceso protegido
                is_protected = self.is_protected_process(process_info['name'])
                status = "🔒 Protegido" if is_protected else " Seguro"
                
                processes.append({
                    'name': process_info['name'],
                    'memory_mb': memory_mb,
                    'pid': process_info['pid'],
                    'protected': is_protected,
                    'status': status
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Ordenar por uso de memoria y devolver top N
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        return processes[:limit]
    
    def is_protected_process(self, process_name):
        """Verifica si un proceso está en la lista de protegidos"""
        if not process_name:
            return True
            
        process_name_lower = process_name.lower()
        
        # Verificar lista blanca exacta
        if process_name_lower in self.protected_processes:
            return True
            
        # Verificar patrones en la lista blanca
        for protected in self.protected_processes:
            if protected in process_name_lower:
                return True
                
        return False
    
    def is_closeable_process(self, process_name):
        """Verifica si un proceso es seguro para cerrar"""
        if not process_name or self.is_protected_process(process_name):
            return False
            
        process_name_lower = process_name.lower()
        
        # Verificar patrones de procesos seguros para cerrar
        for pattern in self.closeable_patterns:
            if pattern.lower() in process_name_lower:
                return True
                
        return False
    
    def get_closeable_processes(self):
        """Obtiene procesos que se pueden cerrar de forma segura"""
        closeable = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                process_info = proc.info
                process_name = process_info['name']
                
                if self.is_closeable_process(process_name):
                    memory_mb = process_info['memory_info'].rss / (1024 * 1024)
                    closeable.append({
                        'name': process_name,
                        'pid': process_info['pid'],
                        'memory_mb': memory_mb
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Agrupar por nombre de proceso
        grouped = defaultdict(list)
        for proc in closeable:
            grouped[proc['name']].append(proc)
        
        # Crear lista final con totales
        final_list = []
        for name, processes in grouped.items():
            total_memory = sum(p['memory_mb'] for p in processes)
            final_list.append({
                'name': name,
                'processes': processes,
                'total_memory_mb': total_memory,
                'count': len(processes)
            })
        
        # Ordenar por memoria total
        final_list.sort(key=lambda x: x['total_memory_mb'], reverse=True)
        return final_list
    
    def update_ram_info(self):
        """Actualiza la información de RAM en la interfaz"""
        def update():
            while True:
                try:
                    ram_info = self.get_ram_info()
                    used_gb = ram_info['used'] / (1024**3)
                    total_gb = ram_info['total'] / (1024**3)
                    
                    # Actualizar etiqueta
                    ram_text = f"RAM: {used_gb:.1f} GB / {total_gb:.1f} GB ({ram_info['percent']:.1f}%)"
                    self.ram_label.config(text=ram_text)
                    
                    # Actualizar barra de progreso
                    self.ram_progress.config(value=ram_info['percent'])
                    
                    # Cambiar color según el uso
                    if ram_info['percent'] > 80:
                        style = ttk.Style()
                        style.configure("red.Horizontal.TProgressbar", background='red')
                        self.ram_progress.config(style="red.Horizontal.TProgressbar")
                    elif ram_info['percent'] > 60:
                        style = ttk.Style()
                        style.configure("yellow.Horizontal.TProgressbar", background='orange')
                        self.ram_progress.config(style="yellow.Horizontal.TProgressbar")
                    else:
                        style = ttk.Style()
                        style.configure("green.Horizontal.TProgressbar", background='green')
                        self.ram_progress.config(style="green.Horizontal.TProgressbar")
                    
                except Exception as e:
                    print(f"Error actualizando RAM: {e}")
                
                time.sleep(2)  # Actualizar cada 2 segundos
        
        # Ejecutar en hilo separado
        thread = threading.Thread(target=update, daemon=True)
        thread.start()
    
    def refresh_data(self):
        """Actualiza la tabla de procesos"""
        # Limpiar tabla
        for item in self.processes_tree.get_children():
            self.processes_tree.delete(item)
        
        # Obtener y mostrar procesos
        try:
            top_processes = self.get_top_processes(10)  # Mostrar más procesos
            
            for proc in top_processes:
                self.processes_tree.insert('', 'end', values=(
                    proc['name'],
                    f"{proc['memory_mb']:.1f}",
                    proc['status']
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener procesos: {e}")
    
    def analyze_ram_liberation(self):
        """Analiza qué procesos se pueden cerrar para liberar RAM"""
        try:
            closeable = self.get_closeable_processes()
            
            if not closeable:
                messagebox.showinfo("Análisis completo", 
                                  "🎉 No se encontraron procesos seguros para cerrar.\n"
                                  "Tu sistema está optimizado o solo tienes aplicaciones esenciales ejecutándose.")
                return
            
            # Calcular RAM total que se puede liberar
            total_ram_mb = sum(proc['total_memory_mb'] for proc in closeable)
            
            # Crear ventana de confirmación
            self.show_liberation_dialog(closeable, total_ram_mb)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en el análisis: {e}")
    
    def show_liberation_dialog(self, closeable_processes, total_ram_mb):
        """Muestra diálogo de confirmación para liberar RAM"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirmar liberación de RAM")
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Marco principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, 
                               text=f"💾 Se pueden liberar {total_ram_mb:.1f} MB de RAM",
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Información
        info_label = ttk.Label(main_frame, 
                              text="Los siguientes procesos seguros pueden cerrarse:",
                              font=('Arial', 10))
        info_label.pack(pady=(0, 10))
        
        # Lista de procesos
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ('Aplicación', 'Instancias', 'RAM (MB)')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        tree.heading('Aplicación', text='Aplicación')
        tree.heading('Instancias', text='Instancias')
        tree.heading('RAM (MB)', text='RAM (MB)')
        
        tree.column('Aplicación', width=250)
        tree.column('Instancias', width=80, anchor='center')
        tree.column('RAM (MB)', width=100, anchor='center')
        
        # Scrollbar
        scrollbar_dialog = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_dialog.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_dialog.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Llenar lista
        for proc in closeable_processes:
            tree.insert('', 'end', values=(
                proc['name'],
                proc['count'],
                f"{proc['total_memory_mb']:.1f}"
            ))
        
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10)
        
        def close_processes():
            try:
                closed_count = 0
                freed_memory = 0
                
                for proc_group in closeable_processes:
                    for process in proc_group['processes']:
                        try:
                            p = psutil.Process(process['pid'])
                            if p.is_running():
                                p.terminate()
                                closed_count += 1
                                freed_memory += process['memory_mb']
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                
                dialog.destroy()
                messagebox.showinfo("Liberación completada", 
                                  f"✅ Se cerraron {closed_count} procesos.\n"
                                  f"💾 Se liberaron aproximadamente {freed_memory:.1f} MB de RAM.")
                
                # Actualizar datos
                self.refresh_data()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cerrar procesos: {e}")
        
        ttk.Button(buttons_frame, text="✅ Liberar RAM", 
                  command=close_processes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="❌ Cancelar", 
                  command=dialog.destroy).pack(side=tk.LEFT)
        
        # Advertencia
        warning_label = ttk.Label(main_frame, 
                                 text="⚠️ Solo se cerrarán aplicaciones seguras (navegadores, juegos, reproductores)",
                                 font=('Arial', 9), foreground='orange')
        warning_label.pack(pady=(10, 0))
    
    def run(self):
        """Ejecuta la aplicación"""
        # Cargar datos iniciales
        self.refresh_data()
        
        # Iniciar loop principal
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = RAMCleaner()
        app.run()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        input("Presiona Enter para salir...")