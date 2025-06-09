import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel
import os
import threading
import time
import tempfile
import subprocess
import platform
import pdf2image
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import shutil
import re
import csv
from datetime import datetime

class BankStatementProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesador de Estados de Cuenta Bancarios")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Variables de estado
        self.pdf_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status = tk.StringVar(value="Esperando archivo...")
        self.progress = tk.DoubleVar(value=0)
        self.processing = False
        self.temp_dir = None

        # Configuración fija
        self.language_var = tk.StringVar(value="spa")
        self.dpi_var = tk.IntVar(value=300)
        self.preprocess_var = tk.BooleanVar(value=True)
        self.save_images_var = tk.BooleanVar(value=False)
        self.output_format_var = tk.StringVar(value="csv")

        # Selección de páginas
        self.page_selection_var = tk.StringVar(value="all")
        self.page_range_var = tk.StringVar()
        self.specific_pages_var = tk.StringVar()

        # Lista para transacciones
        self.all_transactions = []

        # Construir UI
        self.create_widgets()
        self.center_window()
        self.check_dependencies()

    def center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def check_dependencies(self):
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            self.show_error_with_instructions("Tesseract OCR no encontrado", "Este programa requiere Tesseract OCR.")
        if platform.system() != "Windows" and not shutil.which("pdftoppm"):
            self.show_error_with_instructions("Poppler no encontrado", "Este programa requiere Poppler (pdftoppm).")

    def show_error_with_instructions(self, title, message):
        if not messagebox.askokcancel(title, message + "\n\nDesea continuar?" ):
            self.root.destroy()

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Procesador de Estados de Cuenta Bancarios", font=("Arial",16,"bold")).pack(pady=8)

        # Sección archivos
        file_frame = ttk.LabelFrame(main, text="Selección de archivos")
        file_frame.pack(fill=tk.X, pady=4)
        ttk.Label(file_frame, text="PDF o imagen:").grid(row=0,column=0,sticky=tk.W,pady=4)
        ttk.Entry(file_frame, textvariable=self.pdf_path, width=40).grid(row=0,column=1,padx=4)
        ttk.Button(file_frame, text="Examinar...", command=self.select_pdf).grid(row=0,column=2,padx=4)
        ttk.Label(file_frame, text="Guardar como:").grid(row=1,column=0,sticky=tk.W,pady=4)
        ttk.Entry(file_frame, textvariable=self.output_path, width=40).grid(row=1,column=1,padx=4)
        ttk.Button(file_frame, text="Examinar...", command=self.select_output).grid(row=1,column=2)

        # Selección de páginas
        page_frame = ttk.LabelFrame(main, text="Selección de páginas")
        page_frame.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(page_frame, text="Todas", variable=self.page_selection_var, value="all", command=self.update_page_options).grid(row=0,column=0,padx=5)
        ttk.Radiobutton(page_frame, text="Rango", variable=self.page_selection_var, value="range", command=self.update_page_options).grid(row=0,column=1,padx=5)
        self.range_entry = ttk.Entry(page_frame, textvariable=self.page_range_var, width=10)
        self.range_entry.grid(row=0,column=2)
        ttk.Label(page_frame, text="(ej: 1-3)").grid(row=0,column=3)
        ttk.Radiobutton(page_frame, text="Específicas", variable=self.page_selection_var, value="specific", command=self.update_page_options).grid(row=1,column=0,padx=5)
        self.specific_entry = ttk.Entry(page_frame, textvariable=self.specific_pages_var, width=20)
        self.specific_entry.grid(row=1,column=1,columnspan=2)
        ttk.Label(page_frame, text="(ej: 1,4,5)").grid(row=1,column=3)
        self.update_page_options()

        # Botones procesar/cancelar
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=6)
        self.process_button = ttk.Button(btn_frame, text="Procesar", command=self.start_processing)
        self.process_button.pack(side=tk.RIGHT,padx=4)
        self.cancel_button = ttk.Button(btn_frame, text="Cancelar", command=self.cancel_process)
        self.cancel_button.pack(side=tk.RIGHT)

        # Progreso y status
        ttk.Label(main,textvariable=self.status).pack(anchor=tk.W)
        ttk.Progressbar(main,variable=self.progress,mode='determinate').pack(fill=tk.X,padx=4,pady=4)

        # Log
        log_frame = ttk.LabelFrame(main, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame,height=6)
        self.log_text.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        ttk.Scrollbar(log_frame,command=self.log_text.yview).pack(side=tk.RIGHT,fill=tk.Y)
        self.log_text.config(yscrollcommand=self.log_text.yview)

    def update_page_options(self):
        mode = self.page_selection_var.get()
        self.range_entry.config(state="normal" if mode=="range" else "disabled")
        self.specific_entry.config(state="normal" if mode=="specific" else "disabled")

    def get_selected_pages(self, total_pages):
        if self.page_selection_var.get() == "all":
            return list(range(total_pages))
        elif self.page_selection_var.get() == "range":
            try:
                start,end = map(int,self.page_range_var.get().split('-'))
                start = max(1,start)-1
                end = min(total_pages,end)-1
                return list(range(start,end+1))
            except:
                return list(range(total_pages))
        else:
            pages=[]
            for part in self.specific_pages_var.get().split(','):
                try:
                    p=int(part.strip())-1
                    if 0<=p<total_pages: pages.append(p)
                except:
                    pass
            return sorted(set(pages)) if pages else list(range(total_pages))

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF/Imagen","*.pdf;*.png;*.jpg;*.jpeg")])
        if path:
            self.pdf_path.set(path)
            base,_ = os.path.splitext(path)
            ext = self.output_format_var.get()
            suf = {"csv":".csv","json":".json","txt":".txt"}[ext]
            self.output_path.set(base+"_out"+suf)

    def select_output(self):
        ext = self.output_format_var.get()
        filt = ("CSV","*.csv") if ext=="csv" else (("JSON","*.json") if ext=="json" else ("TXT","*.txt"))
        path = filedialog.asksaveasfilename(defaultextension=filt[1],filetypes=[filt])
        if path:
            self.output_path.set(path)

    def start_processing(self):
        if not self.pdf_path.get() or not self.output_path.get():
            messagebox.showerror("Error","Seleciona archivo de entrada y salida.")
            return
        self.process_button.config(state=tk.DISABLED)
        self.all_transactions.clear()
        threading.Thread(target=self.process_statement,daemon=True).start()

    def cancel_process(self):
        if self.processing:
            self.processing=False
            self.status.set("Proceso cancelado")
        else:
            self.root.destroy()

    def process_statement(self):
        try:
            self.processing=True
            self.temp_dir=tempfile.mkdtemp()
            ext=os.path.splitext(self.pdf_path.get())[1].lower()
            if ext in ['.png','.jpg','.jpeg']:
                images=[Image.open(self.pdf_path.get())]
            else:
                images=pdf2image.convert_from_path(self.pdf_path.get(),dpi=self.dpi_var.get())
            total=len(images)
            selected = self.get_selected_pages(total)
            for idx,page in enumerate(selected,1):
                if not self.processing:
                    break
                self.update_progress(idx,len(selected))
                img=images[page]
                img=self.preprocess_image(img)
                text=pytesseract.image_to_string(img,lang=self.language_var.get(),config='--oem 3 --psm 6')
                found=self.parse_bank_statement(text)
                self.log(f"Página {page+1}: {len(found)} transacciones")
                self.all_transactions.extend(found)
            if self.all_transactions:
                self.show_table(self.all_transactions)
            else:
                messagebox.showwarning("Aviso","No se encontraron transacciones.")
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            self.processing=False
            shutil.rmtree(self.temp_dir,ignore_errors=True)
            self.process_button.config(state=tk.NORMAL)
            self.update_progress(1,1)

    def update_progress(self,current,total):
        self.progress.set((current/total)*100)
        self.status.set(f"Procesando {current} de {total}")

    def log(self,msg):
        ts=time.strftime('%H:%M:%S')
        self.log_text.insert(tk.END,f"{ts} - {msg}\n")
        self.log_text.see(tk.END)

    def preprocess_image(self,image):
        if not self.preprocess_var.get():
            return image
        gray=image.convert('L')
        contrast=ImageEnhance.Contrast(gray).enhance(2.0)
        sharp=contrast.filter(ImageFilter.SHARPEN)
        return sharp.point(lambda x:0 if x<150 else 255,'1')

    def parse_bank_statement(self, text):
        # Intento avanzado con patrón de filas completas
        transactions = []
        pattern = re.compile(
            r"(?P<fecha_op>\d{1,2}-[A-Za-z]{3}-\d{4})\s+"
            r"(?P<fecha_cargo>\d{1,2}-[A-Za-z]{3}-\d{4})\s+"
            r"(?P<descripcion>.+?)\s+"
            r"(?P<signo>[+-])?\$\s*(?P<monto>[\d,]+\.\d{2})"
        )
        for line in text.splitlines():
            l = line.strip()
            if not l:
                continue
            m = pattern.match(l)
            if m:
                transactions.append({
                    'fecha_operacion': m.group('fecha_op'),
                    'fecha_cargo':    m.group('fecha_cargo'),
                    'descripcion':    m.group('descripcion').strip(),
                    'signo':          m.group('signo') or '+',
                    'monto':          m.group('monto')
                })
                continue
            # fallback básico
            dates = re.findall(r"\d{1,2}-[A-Za-z]{3}-\d{4}", l)
            amts  = re.findall(r"[-+]?\$\s*[\d,]+\.\d{2}", l)
            if not dates or not amts:
                continue
            raw = amts[-1].replace(' ', '')
            signo = '-' if raw.startswith('-') else '+'
            mont = raw.replace('+','').replace('-','').replace('$','')
            desc_start = l.find(dates[-1]) + len(dates[-1])
            desc_end   = l.find(amts[-1])
            desc = l[desc_start:desc_end].strip()
            transactions.append({
                'fecha_operacion': dates[0],
                'fecha_cargo':    dates[1] if len(dates)>1 else dates[0],
                'descripcion':    re.sub(r"\s+", ' ', desc),
                'signo':          signo,
                'monto':          mont
            })
        return transactions

    def export_to_csv(self, transactions, filename=None):
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Guardar datos en CSV"
            )
            if not filename:  # Si el usuario cancela
                return False
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Fecha de la operación', 'Fecha de cargo', 'Descripción', 'Signo', 'Monto']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for t in transactions:
                    val = float(t['monto'].replace(',', ''))
                    writer.writerow({
                        'Fecha de la operación': t.get('fecha_operacion', ''),
                        'Fecha de cargo': t.get('fecha_cargo', ''),
                        'Descripción': t.get('descripcion', ''),
                        'Signo': t.get('signo', ''),
                        'Monto': f"${val:,.2f}"
                    })
            
            messagebox.showinfo("Exportación Exitosa", f"Los datos han sido exportados a:\n{filename}")
            return True
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"Error al exportar los datos: {e}")
            return False

    def show_table(self, transactions):
        win = Toplevel(self.root)
        win.title("DESGLOSE DE MOVIMIENTOS")
        win.geometry("900x500")
        title_txt = (
            "DESGLOSE DE MOVIMIENTOS\n"
            "CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)\n"
            "Tarjeta Titular 5532530019430901"
        )
        lbl = tk.Label(win, text=title_txt, bg='#D32F2F', fg='white', font=('Arial',12,'bold'), justify='center')
        lbl.pack(fill=tk.X)
        
        # Botón para exportar a CSV
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=5)
        export_btn = ttk.Button(
            btn_frame, 
            text="Exportar a CSV", 
            command=lambda: self.export_to_csv(transactions)
        )
        export_btn.pack(side=tk.RIGHT, padx=10)
        
        cols = ["Fecha de la operación", "Fecha de cargo", "Descripción", "Signo", "Monto"]
        tree = ttk.Treeview(win, columns=cols, show='headings')
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        scrollbar.place(relx=1, rely=0.5, relheight=0.7, anchor="e")
        tree.configure(yscrollcommand=scrollbar.set)
        
        style = ttk.Style(win)
        style.configure('Treeview.Heading', background='#D32F2F', foreground='white', font=('Arial',10,'bold'))
        widths = [120, 120, 380, 60, 100]
        for c, w in zip(cols, widths):
            anchor = tk.W if c == 'Descripción' else tk.CENTER
            tree.heading(c, text=c)
            tree.column(c, anchor=anchor, width=w)
        total_c = 0.0; total_a = 0.0
        for t in transactions:
            val = float(t['monto'].replace(',', ''))
            if t['signo'] == '-': total_a += val
            else: total_c += val
            tree.insert('', tk.END, values=[t.get('fecha_operacion', ''), t.get('fecha_cargo', ''), t.get('descripcion', ''), t.get('signo', ''), f"${val:,.2f}"])
        tot_frame = ttk.Frame(win)
        tot_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(tot_frame, text="Total Cargos", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=200)
        ttk.Label(tot_frame, text='+', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Label(tot_frame, text=f"${total_c:,.2f}", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=20)
        ttk.Label(tot_frame, text="Total Abonos", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=40)
        ttk.Label(tot_frame, text='-', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Label(tot_frame, text=f"${total_a:,.2f}", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=20)

if __name__ == '__main__':
    root = tk.Tk()
    app = BankStatementProcessorApp(root)
    root.mainloop()