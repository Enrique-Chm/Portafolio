import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psutil
import threading
import time
import subprocess
import os
import platform
from operator import attrgetter
import sys
import traceback

# Fix para PyInstaller - Ruta base de recursos
def resource_path(relative_path):
    """ Obtener la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Función para verificar si estamos ejecutando desde PyInstaller
def is_pyinstaller():
    """Comprueba si la aplicación está siendo ejecutada desde un paquete PyInstaller"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

class RAMMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Memoria RAM")
        self.root.geometry("600x600")
        self.root.resizable(True, True)
        
        # Icono de la aplicación (opcional)
        try:
            if platform.system() == "Windows":
                icon_path = resource_path("icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"No se pudo cargar el icono: {str(e)}")  # Registro del error
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", background="#4CAF50", foreground="black", font=("Arial", 10, "bold"))
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        
        # Marco principal
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        self.title_label = ttk.Label(self.main_frame, text="Monitor de Uso de Memoria RAM", font=("Arial", 14, "bold"))
        self.title_label.pack(pady=10)
        
        # Marco para la barra de progreso
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        # Barra de progreso para mostrar el uso de RAM
        self.ram_label = ttk.Label(self.progress_frame, text="Uso de RAM:")
        self.ram_label.pack(anchor=tk.W)
        
        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=550, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        self.percent_label = ttk.Label(self.progress_frame, text="0%")
        self.percent_label.pack(anchor=tk.E)
        
        # Información detallada
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.X, pady=10)
        
        self.total_ram_label = ttk.Label(self.info_frame, text="RAM Total: ")
        self.total_ram_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.used_ram_label = ttk.Label(self.info_frame, text="RAM Usada: ")
        self.used_ram_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.free_ram_label = ttk.Label(self.info_frame, text="RAM Libre: ")
        self.free_ram_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # Etiqueta para mostrar la cantidad de memoria que se puede liberar
        self.releasable_frame = ttk.Frame(self.main_frame)
        self.releasable_frame.pack(fill=tk.X, pady=5)
        
        self.releasable_label = ttk.Label(self.releasable_frame, text="Memoria liberablе: Calculando...", font=("Arial", 10, "bold"))
        self.releasable_label.pack(anchor=tk.W)
        
        # Lista de procesos que consumen más RAM
        self.processes_frame = ttk.LabelFrame(self.main_frame, text="Procesos con mayor consumo de RAM")
        self.processes_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Crear un widget de texto con scroll para mostrar los procesos
        self.processes_text = scrolledtext.ScrolledText(self.processes_frame, wrap=tk.WORD, width=50, height=10)
        self.processes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Botón para liberar memoria
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(fill=tk.X, pady=10)
        
        self.release_btn = ttk.Button(self.btn_frame, text="Liberar Espacio", command=self.release_memory)
        self.release_btn.pack(pady=10)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="", font=("Arial", 9, "italic"))
        self.status_label.pack(fill=tk.X, pady=5)
        
        # Variable para almacenar la memoria liberable estimada
        self.releasable_memory = 0
        
        # Iniciar el hilo para monitorear la RAM
        self.running = True
        self.thread = threading.Thread(target=self.update_ram_usage)
        self.thread.daemon = True
        self.thread.start()
        
        # Asegurarse de que el hilo se detenga cuando la ventana se cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def get_ram_info(self):
        """Obtiene información sobre el uso de RAM."""
        memory = psutil.virtual_memory()
        total = memory.total / (1024 ** 3)  # Convertir a GB
        used = memory.used / (1024 ** 3)
        free = memory.available / (1024 ** 3)
        percent = memory.percent
        
        return total, used, free, percent
    
    def get_process_memory_info(self):
        """Obtiene información sobre el uso de memoria de los procesos."""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                process_info = proc.info
                memory_mb = proc.memory_info().rss / (1024 * 1024)  # Convertir a MB
                
                processes.append({
                    'pid': process_info['pid'],
                    'name': process_info['name'],
                    'memory_percent': process_info['memory_percent'],
                    'memory_mb': memory_mb
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Ordenar procesos por uso de memoria (de mayor a menor)
        processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        
        return processes[:15]  # Devolver los 15 procesos con mayor uso
    
    def estimate_releasable_memory(self):
        """Estima la cantidad de memoria que puede ser liberada."""
        releasable = 0
        non_essential = ["chrome", "firefox", "edge", "spotify", "discord", "teams", 
                        "slack", "skype", "vlc", "itunes", "steam", "epic", "telegram"]
        
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                # Verificar si el proceso es no esencial
                if any(app.lower() in proc.info['name'].lower() for app in non_essential):
                    # Sumar la memoria que usa el proceso
                    releasable += proc.info['memory_info'].rss
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Agregar una estimación para la limpieza de caché del sistema (aproximadamente 5% de la RAM usada)
        system_cache_estimate = psutil.virtual_memory().used * 0.05
        releasable += system_cache_estimate
        
        return releasable / (1024 ** 3)  # Convertir a GB
    
    def update_ram_usage(self):
        """Actualiza continuamente la información de uso de RAM."""
        while self.running:
            total, used, free, percent = self.get_ram_info()
            
            # Obtener información de procesos
            processes = self.get_process_memory_info()
            
            # Estimar memoria liberable
            self.releasable_memory = self.estimate_releasable_memory()
            
            # Actualizar barra de progreso
            self.progress['value'] = percent
            self.percent_label.config(text=f"{percent:.1f}%")
            
            # Actualizar etiquetas
            self.total_ram_label.config(text=f"RAM Total: {total:.2f} GB")
            self.used_ram_label.config(text=f"RAM Usada: {used:.2f} GB ({percent:.1f}%)")
            self.free_ram_label.config(text=f"RAM Libre: {free:.2f} GB")
            self.releasable_label.config(text=f"Memoria liberablе: {self.releasable_memory:.2f} GB aproximadamente")
            
            # Actualizar lista de procesos
            self.update_process_list(processes)
            
            # Cambiar color según el uso
            if percent < 60:
                self.progress['style'] = 'green.Horizontal.TProgressbar'
            elif percent < 80:
                self.progress['style'] = 'yellow.Horizontal.TProgressbar'
            else:
                self.progress['style'] = 'red.Horizontal.TProgressbar'
            
            time.sleep(2)  # Actualizar cada 2 segundos
    
    def update_process_list(self, processes):
        """Actualiza la lista de procesos en el widget de texto."""
        self.processes_text.config(state=tk.NORMAL)
        self.processes_text.delete(1.0, tk.END)
        
        # Agregar encabezado
        self.processes_text.insert(tk.END, "PID\tNombre\t\t\tUso de RAM (MB)\t% de RAM\n")
        self.processes_text.insert(tk.END, "-" * 70 + "\n")
        
        # Agregar procesos
        for proc in processes:
            name = proc['name'][:18] + "..." if len(proc['name']) > 20 else proc['name'].ljust(20)
            self.processes_text.insert(tk.END, 
                f"{proc['pid']}\t{name}\t{proc['memory_mb']:.1f} MB\t\t{proc['memory_percent']:.2f}%\n")
        
        self.processes_text.config(state=tk.DISABLED)  # Hacer el texto de solo lectura
    
    def release_memory(self):
        """Intenta liberar memoria RAM."""
        self.status_label.config(text="Liberando memoria...")
        
        # Guardar el valor anterior para la comparación
        prev_memory_usage = psutil.virtual_memory().percent
        
        # Crear un hilo para el proceso de liberación
        thread = threading.Thread(target=self._perform_memory_cleanup)
        thread.daemon = True
        thread.start()
    
    def _perform_memory_cleanup(self):
        """Realiza las tareas de limpieza de memoria en segundo plano."""
        sistema = platform.system()
        
        try:
            if sistema == "Windows":
                # En Windows, llamar al recolector de basura y ejecutar algunos comandos
                import gc
                gc.collect()  # Python garbage collector
                
                # Obtener la ruta base de la aplicación empaquetada (si está en modo PyInstaller)
                base_path = getattr(sys, '_MEIPASS', None)
                
                # Limpiar archivos temporales de Windows evitando la carpeta de PyInstaller
                if base_path and base_path.startswith(os.environ.get('TEMP', '')):
                    # Si estamos en modo PyInstaller, evitar borrar la carpeta de PyInstaller
                    temp_folder = os.environ.get('TEMP', '')
                    meipass_folder = os.path.basename(base_path)
                    # Usar un comando más seguro que evite borrar la carpeta _MEI
                    subprocess.call(f'powershell -Command "Get-ChildItem -Path $env:TEMP -Exclude {meipass_folder} | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"', shell=True)
                else:
                    # En modo desarrollo, podemos limpiar normalmente
                    subprocess.call('powershell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"', shell=True)
                    subprocess.call('del /f /s /q %temp%\\*.*', shell=True)
                
                # Intenta liberar memoria caché del sistema
                subprocess.call('powershell -Command "& {[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers();}"', shell=True)
                
            elif sistema == "Linux":
                # En Linux, liberar caché
                os.system("sync && echo 3 | sudo tee /proc/sys/vm/drop_caches")
                
            elif sistema == "Darwin":  # macOS
                # En macOS, limpiar caché DNS y otras cachés
                os.system("sudo dscacheutil -flushcache")
                os.system("sudo killall -HUP mDNSResponder")
                
            # Terminar procesos que no son esenciales
            memory_freed = self._terminate_non_essential_processes()
            
            # Esperar un poco y obtener el nuevo uso de RAM
            time.sleep(2)
            _, _, _, new_percent = self.get_ram_info()
            
            # Obtener la diferencia
            prev_memory_usage = psutil.virtual_memory().percent
            memory_difference = self.releasable_memory - memory_freed/1024**3
            
            # Actualizar la etiqueta de estado
            self.root.after(0, lambda: self.status_label.config(
                text=f"¡Limpieza completada! Se liberaron aproximadamente {memory_freed/1024**3:.2f} GB. Uso de RAM actual: {new_percent:.1f}%"))
                
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(
                text=f"Error al liberar memoria: {str(e)}"))
    
    def _terminate_non_essential_processes(self):
        """Termina procesos que no son esenciales para liberar memoria. Devuelve los bytes liberados."""
        sistema = platform.system()
        memory_freed = 0
        
        try:
            if sistema == "Windows":
                # Lista de procesos comunes que pueden ser cerrados
                non_essential = ["chrome.exe", "firefox.exe", "spotify.exe", "discord.exe", 
                                "msedge.exe", "teams.exe", "slack.exe", "skype.exe", 
                                "vlc.exe", "itunes.exe", "steam.exe", "epicgameslauncher.exe", "telegram.exe"]
                
                for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                    try:
                        if any(app.lower() in proc.info['name'].lower() for app in non_essential):
                            # Verificar si no es el proceso actual
                            if proc.pid != os.getpid():
                                # Almacenar cuánta memoria usa antes de terminarlo
                                memory_freed += proc.info['memory_info'].rss
                                proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            
            elif sistema == "Linux":
                # Procesos comunes en Linux
                non_essential = ["chrome", "firefox", "spotify", "discord", "teams", "slack", "skype"]
                
                for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                    try:
                        for app in non_essential:
                            if app in proc.info['name'].lower():
                                if proc.pid != os.getpid():
                                    memory_freed += proc.info['memory_info'].rss
                                    proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            
            elif sistema == "Darwin":  # macOS
                # Procesos comunes en macOS
                non_essential = ["Chrome", "Firefox", "Spotify", "Discord", "Teams", "Slack", "Skype"]
                
                for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                    try:
                        for app in non_essential:
                            if app in proc.info['name']:
                                if proc.pid != os.getpid():
                                    memory_freed += proc.info['memory_info'].rss
                                    proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
        
        except Exception as e:
            print(f"Error al terminar procesos: {str(e)}")
        
        return memory_freed
    
    def on_closing(self):
        """Maneja el evento de cierre de la ventana."""
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    try:
        # Crear y configurar estilos para las barras de progreso
        root = tk.Tk()
        style = ttk.Style(root)
        style.theme_use("default")
        
        # Configurar estilos personalizados para la barra de progreso
        style.configure("green.Horizontal.TProgressbar", background='#4CAF50')
        style.configure("yellow.Horizontal.TProgressbar", background='#FFC107')
        style.configure("red.Horizontal.TProgressbar", background='#F44336')
        
        # Iniciar la aplicación
        app = RAMMonitor(root)
        root.mainloop()
    except Exception as e:
        error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}"
        try:
            # Intentar mostrar error gráficamente
            messagebox.showerror("Error al iniciar la aplicación", error_msg)
        except:
            # Si falla el método gráfico, mostrar en consola
            print(error_msg)