"""
Interfaz de usuario para lector de códigos de barras
Maneja la captura, decodificación y procesamiento de códigos de barras
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
import threading
import queue
import time

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pyzbar.pyzbar as pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from modules.inventory.product import ProductManager
from ui.ui_helpers import create_styled_frame, create_input_frame
from core.database import ejecutar_consulta_segura

class BarcodeReaderUI:
    """Interfaz principal para lector de códigos de barras"""
    
    def __init__(self, parent_window, callback_function: Optional[Callable] = None):
        self.parent = parent_window
        self.product_manager = ProductManager()
        self.callback_function = callback_function  # Función a llamar cuando se escanea un código
        
        # Variables de control
        self.camera_active = False
        self.camera = None
        self.camera_index = 0
        self.scan_queue = queue.Queue()
        self.last_scan_time = 0
        self.scan_cooldown = 2  # Segundos entre escaneos del mismo código
        self.last_scanned_code = ""
        
        # Variables de configuración
        self.config_vars = {
            'auto_search': tk.BooleanVar(value=True),
            'beep_enabled': tk.BooleanVar(value=True),
            'continuous_scan': tk.BooleanVar(value=True),
            'camera_device': tk.StringVar(value="0"),
            'scan_timeout': tk.IntVar(value=30)
        }
        
        # Historial de escaneos
        self.scan_history = []
        
        self.check_dependencies()
        self.setup_ui()
        self.load_camera_devices()
    
    def check_dependencies(self):
        """Verifica las dependencias necesarias"""
        missing_deps = []
        
        if not CV2_AVAILABLE:
            missing_deps.append("opencv-python")
        if not PYZBAR_AVAILABLE:
            missing_deps.append("pyzbar")
        if not PIL_AVAILABLE:
            missing_deps.append("Pillow")
        
        if missing_deps:
            messagebox.showwarning(
                "Dependencias Faltantes",
                f"Las siguientes librerías son necesarias para el lector de códigos:\n"
                f"{', '.join(missing_deps)}\n\n"
                f"Instálelas con: pip install {' '.join(missing_deps)}"
            )
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título y controles principales
        self.setup_header()
        
        # Frame principal dividido
        main_content = ttk.Frame(self.main_frame)
        main_content.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Panel de cámara (lado izquierdo)
        self.setup_camera_panel(main_content)
        
        # Panel de información (lado derecho)
        self.setup_info_panel(main_content)
        
        # Panel de configuración y historial (abajo)
        self.setup_bottom_panels()
    
    def setup_header(self):
        """Configura el encabezado con título y controles"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Título
        ttk.Label(header_frame, text="Lector de Códigos de Barras", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Controles principales
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        self.start_button = ttk.Button(controls_frame, text="Iniciar Cámara", 
                                      command=self.toggle_camera)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Escanear Archivo", 
                  command=self.scan_from_file).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Entrada Manual", 
                  command=self.manual_entry).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Configuración", 
                  command=self.show_config).pack(side=tk.LEFT, padx=5)
    
    def setup_camera_panel(self, parent):
        """Configura el panel de la cámara"""
        camera_frame = create_styled_frame(parent, "Vista de Cámara")
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Canvas para mostrar la cámara
        self.camera_canvas = tk.Canvas(camera_frame, width=640, height=480, 
                                      bg='black', relief=tk.SUNKEN, bd=2)
        self.camera_canvas.pack(padx=10, pady=10)
        
        # Estado de la cámara
        status_frame = ttk.Frame(camera_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(status_frame, text="Estado:").pack(side=tk.LEFT)
        self.camera_status = ttk.Label(status_frame, text="Desconectada", 
                                      foreground='red', font=('Arial', 10, 'bold'))
        self.camera_status.pack(side=tk.LEFT, padx=5)
        
        # Indicador de escaneo
        self.scan_indicator = ttk.Label(status_frame, text="●", 
                                       foreground='gray', font=('Arial', 20))
        self.scan_indicator.pack(side=tk.RIGHT)
        
        # Texto de instrucciones
        instructions = tk.Text(camera_frame, height=3, wrap=tk.WORD, 
                              font=('Arial', 9), state=tk.DISABLED)
        instructions.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        instructions.config(state=tk.NORMAL)
        instructions.insert(tk.END, 
            "Instrucciones:\n"
            "• Apunte la cámara hacia el código de barras\n"
            "• Mantenga el código centrado y bien iluminado\n"
            "• El escaneo es automático cuando se detecta un código válido")
        instructions.config(state=tk.DISABLED)
    
    def setup_info_panel(self, parent):
        """Configura el panel de información del producto"""
        info_frame = create_styled_frame(parent, "Información del Producto")
        info_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Información del último código escaneado
        scan_info_frame = ttk.LabelFrame(info_frame, text="Último Escaneo")
        scan_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Variables para información de escaneo
        self.scan_info_vars = {
            'codigo_barras': tk.StringVar(),
            'tipo_codigo': tk.StringVar(),
            'fecha_escaneo': tk.StringVar(),
            'tiempo_procesamiento': tk.StringVar()
        }
        
        row = 0
        for field, var in self.scan_info_vars.items():
            ttk.Label(scan_info_frame, text=f"{field.replace('_', ' ').title()}:").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(scan_info_frame, textvariable=var, background='white', 
                     relief=tk.SUNKEN, width=25).grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            row += 1
        
        scan_info_frame.columnconfigure(1, weight=1)
        
        # Información del producto encontrado
        product_info_frame = ttk.LabelFrame(info_frame, text="Producto Encontrado")
        product_info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Variables para información del producto
        self.product_info_vars = {
            'codigo_interno': tk.StringVar(),
            'nombre': tk.StringVar(),
            'descripcion': tk.StringVar(),
            'categoria': tk.StringVar(),
            'precio_venta': tk.StringVar(),
            'stock_actual': tk.StringVar(),
            'estado': tk.StringVar()
        }
        
        row = 0
        for field, var in self.product_info_vars.items():
            ttk.Label(product_info_frame, text=f"{field.replace('_', ' ').title()}:").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(product_info_frame, textvariable=var, background='white', 
                     relief=tk.SUNKEN, width=25).grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            row += 1
        
        product_info_frame.columnconfigure(1, weight=1)
        
        # Imagen del producto (si está disponible)
        image_frame = ttk.LabelFrame(info_frame, text="Imagen")
        image_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.product_image_label = ttk.Label(image_frame, text="Sin imagen", 
                                            background='lightgray', width=30, 
                                            anchor=tk.CENTER)
        self.product_image_label.pack(padx=10, pady=10)
        
        # Botones de acción
        actions_frame = ttk.Frame(info_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(actions_frame, text="Ver Detalles", 
                  command=self.view_product_details).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Editar Producto", 
                  command=self.edit_product).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Agregar al Carrito", 
                  command=self.add_to_cart).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Movimiento Stock", 
                  command=self.stock_movement).pack(fill=tk.X, pady=2)
    
    def setup_bottom_panels(self):
        """Configura los paneles inferiores"""
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel de configuración rápida (izquierda)
        self.setup_quick_config(bottom_frame)
        
        # Panel de historial (derecha)
        self.setup_history_panel(bottom_frame)
    
    def setup_quick_config(self, parent):
        """Configura el panel de configuración rápida"""
        config_frame = create_styled_frame(parent, "Configuración Rápida")
        config_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        config_content = ttk.Frame(config_frame)
        config_content.pack(fill=tk.BOTH, padx=10, pady=5)
        
        # Checkboxes de configuración
        ttk.Checkbutton(config_content, text="Búsqueda automática", 
                       variable=self.config_vars['auto_search']).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(config_content, text="Sonido de confirmación", 
                       variable=self.config_vars['beep_enabled']).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(config_content, text="Escaneo continuo", 
                       variable=self.config_vars['continuous_scan']).pack(anchor=tk.W, pady=2)
        
        # Selección de cámara
        camera_frame = ttk.Frame(config_content)
        camera_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(camera_frame, text="Cámara:").pack(side=tk.LEFT)
        self.camera_combo = ttk.Combobox(camera_frame, textvariable=self.config_vars['camera_device'],
                                        width=10, state="readonly")
        self.camera_combo.pack(side=tk.LEFT, padx=5)
        self.camera_combo.bind('<<ComboboxSelected>>', self.on_camera_changed)
        
        # Timeout de escaneo
        timeout_frame = ttk.Frame(config_content)
        timeout_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(timeout_frame, text="Timeout (s):").pack(side=tk.LEFT)
        ttk.Entry(timeout_frame, textvariable=self.config_vars['scan_timeout'], 
                 width=10).pack(side=tk.LEFT, padx=5)
    
    def setup_history_panel(self, parent):
        """Configura el panel de historial de escaneos"""
        history_frame = create_styled_frame(parent, "Historial de Escaneos")
        history_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Controles del historial
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(history_controls, text="Limpiar", 
                  command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_controls, text="Exportar", 
                  command=self.export_history).pack(side=tk.LEFT, padx=5)
        
        # Lista de historial
        history_columns = ('hora', 'codigo', 'tipo', 'producto', 'accion')
        self.history_tree = ttk.Treeview(history_frame, columns=history_columns, 
                                        show='headings', height=8)
        
        # Configurar columnas
        self.history_tree.heading('hora', text='Hora')
        self.history_tree.heading('codigo', text='Código')
        self.history_tree.heading('tipo', text='Tipo')
        self.history_tree.heading('producto', text='Producto')
        self.history_tree.heading('accion', text='Acción')
        
        # Anchos de columnas
        self.history_tree.column('hora', width=80)
        self.history_tree.column('codigo', width=120)
        self.history_tree.column('tipo', width=80)
        self.history_tree.column('producto', width=200)
        self.history_tree.column('accion', width=100)
        
        # Scrollbar
        history_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, 
                                      command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))
        
        # Bind eventos
        self.history_tree.bind('<Double-1>', self.on_history_double_click)
    
    def load_camera_devices(self):
        """Carga los dispositivos de cámara disponibles"""
        try:
            if not CV2_AVAILABLE:
                self.camera_combo['values'] = ["No disponible"]
                return
            
            devices = []
            # Intentar detectar cámaras disponibles
            for i in range(5):  # Probar primeros 5 índices
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    devices.append(f"Cámara {i}")
                    cap.release()
            
            if not devices:
                devices = ["No se encontraron cámaras"]
            
            self.camera_combo['values'] = devices
            if devices and devices[0] != "No se encontraron cámaras":
                self.camera_combo.current(0)
            
        except Exception as e:
            self.camera_combo['values'] = ["Error detectando cámaras"]
    
    def toggle_camera(self):
        """Activa/desactiva la cámara"""
        if self.camera_active:
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        """Inicia la cámara"""
        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV no está disponible")
            return
        
        try:
            camera_index = int(self.config_vars['camera_device'].get().split()[-1])
        except:
            camera_index = 0
        
        self.camera = cv2.VideoCapture(camera_index)
        
        if not self.camera.isOpened():
            messagebox.showerror("Error", "No se pudo abrir la cámara")
            return
        
        self.camera_active = True
        self.start_button.config(text="Detener Cámara")
        self.camera_status.config(text="Conectada", foreground='green')
        
        # Iniciar hilo de captura
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
        
        # Iniciar procesamiento de escaneos
        self.parent.after(100, self.process_scans)
    
    def stop_camera(self):
        """Detiene la cámara"""
        self.camera_active = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.start_button.config(text="Iniciar Cámara")
        self.camera_status.config(text="Desconectada", foreground='red')
        self.scan_indicator.config(foreground='gray')
        
        # Limpiar canvas
        self.camera_canvas.delete("all")
        self.camera_canvas.create_text(320, 240, text="Cámara Desconectada", 
                                      fill='white', font=('Arial', 16))
    
    def camera_loop(self):
        """Bucle principal de captura de cámara"""
        while self.camera_active and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # Redimensionar frame
                frame = cv2.resize(frame, (640, 480))
                
                # Buscar códigos de barras
                if PYZBAR_AVAILABLE:
                    barcodes = pyzbar.decode(frame)
                    
                    for barcode in barcodes:
                        # Dibujar rectángulo alrededor del código
                        x, y, w, h = barcode.rect
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        
                        # Agregar texto del código
                        barcode_data = barcode.data.decode('utf-8')
                        cv2.putText(frame, barcode_data, (x, y - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        # Enviar código para procesamiento
                        current_time = time.time()
                        if (barcode_data != self.last_scanned_code or 
                            current_time - self.last_scan_time > self.scan_cooldown):
                            
                            self.scan_queue.put({
                                'code': barcode_data,
                                'type': barcode.type,
                                'timestamp': datetime.now()
                            })
                            
                            self.last_scanned_code = barcode_data
                            self.last_scan_time = current_time
                
                # Convertir frame para Tkinter
                if PIL_AVAILABLE:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame_rgb)
                    photo = ImageTk.PhotoImage(image)
                    
                    # Actualizar canvas en hilo principal
                    self.parent.after(0, self.update_camera_display, photo)
                
            except Exception as e:
                print(f"Error en camera_loop: {e}")
                break
        
        # Limpiar al salir
        if self.camera:
            self.camera.release()
    
    def update_camera_display(self, photo):
        """Actualiza la visualización de la cámara"""
        try:
            self.camera_canvas.delete("all")
            self.camera_canvas.create_image(320, 240, image=photo)
            # Guardar referencia para evitar garbage collection
            self.camera_canvas.photo = photo
        except Exception as e:
            print(f"Error actualizando display: {e}")
    
    def process_scans(self):
        """Procesa los códigos escaneados"""
        try:
            while not self.scan_queue.empty():
                scan_data = self.scan_queue.get_nowait()
                self.handle_scanned_code(scan_data)
                
                # Indicador visual de escaneo
                self.scan_indicator.config(foreground='green')
                self.parent.after(500, lambda: self.scan_indicator.config(foreground='gray'))
            
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error procesando escaneos: {e}")
        
        # Continuar procesando si la cámara está activa
        if self.camera_active:
            self.parent.after(100, self.process_scans)
    
    def handle_scanned_code(self, scan_data):
        """Maneja un código escaneado"""
        try:
            barcode = scan_data['code']
            barcode_type = scan_data['type']
            timestamp = scan_data['timestamp']
            
            # Actualizar información de escaneo
            self.scan_info_vars['codigo_barras'].set(barcode)
            self.scan_info_vars['tipo_codigo'].set(barcode_type)
            self.scan_info_vars['fecha_escaneo'].set(timestamp.strftime("%H:%M:%S"))
            
            # Reproducir sonido si está habilitado
            if self.config_vars['beep_enabled'].get():
                self.play_beep()
            
            # Buscar producto automáticamente si está habilitado
            product = None
            if self.config_vars['auto_search'].get():
                start_time = time.time()
                product = self.search_product_by_barcode(barcode)
                processing_time = (time.time() - start_time) * 1000
                self.scan_info_vars['tiempo_procesamiento'].set(f"{processing_time:.1f} ms")
            
            # Agregar al historial
            self.add_to_history(barcode, barcode_type, product, timestamp)
            
            # Llamar callback si existe
            if self.callback_function:
                self.callback_function(barcode, product)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando código: {str(e)}")
    
    def search_product_by_barcode(self, barcode):
        """Busca un producto por código de barras"""
        try:
            product = self.product_manager.buscar_por_codigo_barras(barcode)
            
            if product:
                # Actualizar información del producto
                self.product_info_vars['codigo_interno'].set(product.get('codigo', ''))
                self.product_info_vars['nombre'].set(product.get('nombre', ''))
                self.product_info_vars['descripcion'].set(product.get('descripcion', ''))
                self.product_info_vars['categoria'].set(product.get('categoria', ''))
                self.product_info_vars['precio_venta'].set(f"₡{product.get('precio_venta', 0):,.2f}")
                self.product_info_vars['stock_actual'].set(f"{product.get('stock_actual', 0)}")
                self.product_info_vars['estado'].set(product.get('estado', ''))
                
                # TODO: Cargar imagen del producto si existe
                self.product_image_label.config(text="Sin imagen")
                
                return product
            else:
                # Limpiar información si no se encuentra
                for var in self.product_info_vars.values():
                    var.set('')
                self.product_image_label.config(text="Producto no encontrado")
                
                return None
                
        except Exception as e:
            messagebox.showerror("Error", f"Error buscando producto: {str(e)}")
            return None
    
    def add_to_history(self, barcode, barcode_type, product, timestamp):
        """Agrega un escaneo al historial"""
        try:
            product_name = product.get('nombre', 'No encontrado') if product else 'No encontrado'
            action = 'Encontrado' if product else 'No encontrado'
            
            # Agregar a la lista interna
            self.scan_history.append({
                'timestamp': timestamp,
                'barcode': barcode,
                'type': barcode_type,
                'product': product_name,
                'action': action
            })
            
            # Agregar al TreeView
            self.history_tree.insert('', 0, values=(  # Insertar al inicio
                timestamp.strftime("%H:%M:%S"),
                barcode,
                barcode_type,
                product_name[:30] + "..." if len(product_name) > 30 else product_name,
                action
            ))
            
            # Mantener solo los últimos 100 registros
            if len(self.scan_history) > 100:
                self.scan_history.pop()
                # Eliminar último item del TreeView
                items = self.history_tree.get_children()
                if items:
                    self.history_tree.delete(items[-1])
            
        except Exception as e:
            print(f"Error agregando al historial: {e}")
    
    def scan_from_file(self):
        """Escanea código de barras desde archivo de imagen"""
        if not PYZBAR_AVAILABLE or not PIL_AVAILABLE:
            messagebox.showerror("Error", "Dependencias faltantes para escanear archivos")
            return
        
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Cargar imagen
                image = Image.open(file_path)
                
                # Convertir a formato para pyzbar
                image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Buscar códigos
                barcodes = pyzbar.decode(image_cv)
                
                if barcodes:
                    for barcode in barcodes:
                        barcode_data = barcode.data.decode('utf-8')
                        scan_data = {
                            'code': barcode_data,
                            'type': barcode.type,
                            'timestamp': datetime.now()
                        }
                        self.handle_scanned_code(scan_data)
                        break  # Procesar solo el primer código encontrado
                else:
                    messagebox.showinfo("Info", "No se encontraron códigos de barras en la imagen")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error procesando imagen: {str(e)}")
    
    def manual_entry(self):
        """Entrada manual de código de barras"""
        ManualEntryDialog(self.parent, self.handle_manual_code)
    
    def handle_manual_code(self, barcode):
        """Maneja código ingresado manualmente"""
        scan_data = {
            'code': barcode,
            'type': 'MANUAL',
            'timestamp': datetime.now()
        }
        self.handle_scanned_code(scan_data)
    
    def show_config(self):
        """Muestra configuración avanzada"""
        ConfigDialog(self.parent, self.config_vars)
    
    def on_camera_changed(self, event=None):
        """Maneja cambio de cámara"""
        if self.camera_active:
            self.stop_camera()
            self.parent.after(500, self.start_camera)  # Reiniciar después de un momento
    
    def play_beep(self):
        """Reproduce sonido de confirmación"""
        try:
            # Usar sonido del sistema
            import winsound
            winsound.Beep(1000, 200)  # Frecuencia 1000Hz, duración 200ms
        except:
            # Alternativa multiplataforma
            print('\a')  # Bell character
    
    def view_product_details(self):
        """Ver detalles del producto actual"""
        codigo_barras = self.scan_info_vars['codigo_barras'].get()
        if not codigo_barras:
            messagebox.showwarning("Advertencia", "No hay producto seleccionado")
            return
        
        product = self.search_product_by_barcode(codigo_barras)
        if product:
            ProductDetailsDialog(self.parent, product)
        else:
            messagebox.showinfo("Info", "Producto no encontrado")
    
    def edit_product(self):
        """Editar producto actual"""
        codigo_barras = self.scan_info_vars['codigo_barras'].get()
        if not codigo_barras:
            messagebox.showwarning("Advertencia", "No hay producto seleccionado")
            return
        
        # Aquí integrar con el editor de productos
        messagebox.showinfo("Info", "Editor de productos en desarrollo")
    
    def add_to_cart(self):
        """Agregar producto al carrito (para punto de venta)"""
        codigo_barras = self.scan_info_vars['codigo_barras'].get()
        if not codigo_barras:
            messagebox.showwarning("Advertencia", "No hay producto seleccionado")
            return
        
        # Aquí integrar con sistema de ventas
        messagebox.showinfo("Info", "Integración con ventas en desarrollo")
    
    def stock_movement(self):
        """Movimiento de stock del producto"""
        codigo_barras = self.scan_info_vars['codigo_barras'].get()
        if not codigo_barras:
            messagebox.showwarning("Advertencia", "No hay producto seleccionado")
            return
        
        # Aquí integrar con gestión de inventario
        messagebox.showinfo("Info", "Movimiento de stock en desarrollo")
    
    def clear_history(self):
        """Limpia el historial de escaneos"""
        if messagebox.askyesno("Confirmar", "¿Limpiar todo el historial de escaneos?"):
            self.scan_history.clear()
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
    
    def export_history(self):
        """Exporta el historial de escaneos"""
        if not self.scan_history:
            messagebox.showinfo("Info", "No hay historial para exportar")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Exportar Historial",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        
        if file_path:
            try:
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Timestamp', 'Código', 'Tipo', 'Producto', 'Acción'])
                    
                    for scan in reversed(self.scan_history):  # Más recientes primero
                        writer.writerow([
                            scan['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                            scan['barcode'],
                            scan['type'],
                            scan['product'],
                            scan['action']
                        ])
                
                messagebox.showinfo("Éxito", "Historial exportado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {str(e)}")
    
    def on_history_double_click(self, event):
        """Maneja doble clic en historial"""
        selection = self.history_tree.selection()
        if selection:
            item = self.history_tree.item(selection[0])
            barcode = item['values'][1]
            
            # Buscar producto nuevamente
            self.search_product_by_barcode(barcode)
            self.scan_info_vars['codigo_barras'].set(barcode)

# Diálogos auxiliares
class ManualEntryDialog:
    """Diálogo para entrada manual de código"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Entrada Manual de Código")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"400x200+{x}+{y}")
        
        self.setup_dialog()
    
    def setup_dialog(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="Ingrese el código de barras:", 
                 font=('Arial', 12)).pack(pady=10)
        
        self.code_var = tk.StringVar()
        code_entry = ttk.Entry(main_frame, textvariable=self.code_var, 
                              font=('Arial', 14), width=30)
        code_entry.pack(pady=10)
        code_entry.focus()
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=20)
        
        ttk.Button(buttons_frame, text="Cancelar", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Procesar", 
                  command=self.process_code).pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter key
        code_entry.bind('<Return>', lambda e: self.process_code())
    
    def process_code(self):
        code = self.code_var.get().strip()
        if code:
            self.callback(code)
            self.dialog.destroy()
        else:
            messagebox.showwarning("Advertencia", "Ingrese un código válido")

class ConfigDialog:
    """Diálogo de configuración avanzada"""
    
    def __init__(self, parent, config_vars):
        self.config_vars = config_vars
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuración Avanzada")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        messagebox.showinfo("Info", "Configuración avanzada en desarrollo")

class ProductDetailsDialog:
    """Diálogo para mostrar detalles del producto"""
    
    def __init__(self, parent, product):
        self.product = product
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Detalles - {product.get('nombre', '')}")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        messagebox.showinfo("Info", "Detalles del producto en desarrollo")

# Función principal
def mostrar_lector_barras(parent_window, callback=None):
    """Función principal para mostrar el lector de códigos de barras"""
    BarcodeReaderUI(parent_window, callback)
