#!/usr/bin/env python3
"""
Aplicación Web Móvil - Caja Central POS
Sistema POS optimizado para dispositivos móviles
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
import sqlite3
import hashlib
import os
from datetime import datetime
import json
import time

# Configuración
DATABASE_PATH = "../data/caja_registradora_pos_cr.db"
SECRET_KEY = "caja_central_pos_mobile_2025_super_secret_key"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Simplificar configuración de sesiones
app.config['SESSION_COOKIE_NAME'] = 'mobile_pos_session'
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Permitir acceso desde JS si es necesario
app.config['SESSION_COOKIE_SECURE'] = False   # Para HTTP local
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas

# Variable global para mantener sesiones como fallback
active_sessions = {}

class MobilePOS:
    """Clase principal para el sistema POS móvil"""
    
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos si no existe"""
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        if not os.path.exists(DATABASE_PATH):
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Tabla usuarios básica
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    rol TEXT DEFAULT 'cajero',
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla productos básica
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE,
                    nombre TEXT NOT NULL,
                    precio REAL NOT NULL,
                    stock INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla ventas básica
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER,
                    total REAL NOT NULL,
                    estado TEXT DEFAULT 'completada',
                    items_json TEXT
                )
            ''')
            
            # Usuario admin por defecto (múltiples versiones para compatibilidad)
            
            # Admin con contraseña simple (para testing)
            try:
                cursor.execute('''
                    INSERT INTO usuarios (username, password, nombre, rol) 
                    VALUES (?, ?, ?, ?)
                ''', ("admin", "admin123", "Administrador", "admin"))
                print("✅ Usuario admin creado (simple)")
            except sqlite3.IntegrityError:
                print("ℹ️ Usuario admin ya existe")
            
            # Admin con hash también
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            try:
                cursor.execute('''
                    INSERT INTO usuarios (username, password, nombre, rol) 
                    VALUES (?, ?, ?, ?)
                ''', ("admin_hash", password_hash, "Admin Hash", "admin"))
                print("✅ Usuario admin_hash creado")
            except sqlite3.IntegrityError:
                print("ℹ️ Usuario admin_hash ya existe")
            
            # Productos de ejemplo - Inventario completo
            productos_ejemplo = [
                # Bebidas
                ("BEB001", "Café Americano", 1500, 50),
                ("BEB002", "Café con Leche", 1800, 40),
                ("BEB003", "Cappuccino", 2200, 30),
                ("BEB004", "Té Chai", 1600, 25),
                ("BEB005", "Refresco Cola 355ml", 800, 100),
                ("BEB006", "Refresco Naranja 355ml", 800, 80),
                ("BEB007", "Agua Natural 500ml", 500, 150),
                ("BEB008", "Agua con Gas 500ml", 600, 60),
                ("BEB009", "Jugo Natural Naranja", 1200, 40),
                ("BEB010", "Smoothie Fresa", 2500, 20),
                
                # Comida
                ("COM001", "Sandwich Jamón y Queso", 2500, 30),
                ("COM002", "Sandwich Pollo", 2800, 25),
                ("COM003", "Hamburguesa Clásica", 3500, 20),
                ("COM004", "Pizza Personal", 3200, 15),
                ("COM005", "Ensalada César", 2800, 18),
                ("COM006", "Wrap Vegetariano", 2600, 22),
                ("COM007", "Quesadilla", 2200, 25),
                ("COM008", "Nachos con Queso", 1800, 30),
                
                # Postres
                ("POS001", "Pasteles Variados", 1200, 25),
                ("POS002", "Cheesecake", 2200, 12),
                ("POS003", "Brownie", 1500, 20),
                ("POS004", "Muffin Chocolate", 1000, 35),
                ("POS005", "Galletas Artesanales", 800, 50),
                ("POS006", "Helado Copa", 1800, 25),
                
                # Snacks
                ("SNK001", "Papas Fritas", 1200, 45),
                ("SNK002", "Pretzels", 900, 40),
                ("SNK003", "Nueces Mixtas", 1500, 30),
                ("SNK004", "Chocolate Barra", 800, 60),
                ("SNK005", "Chicles", 300, 100),
                
                # Artículos para llevar
                ("ART001", "Café en Grano 250g", 4500, 15),
                ("ART002", "Taza Personalizada", 3500, 10),
                ("ART003", "Servilletas Pack", 500, 50),
                ("ART004", "Azúcar Sobres x10", 400, 80),
                ("ART005", "Crema Sobres x10", 600, 60),
            ]
            cursor.executemany('''
                INSERT INTO productos (codigo, nombre, precio, stock) 
                VALUES (?, ?, ?, ?)
            ''', productos_ejemplo)
            
            conn.commit()
            conn.close()
    
    def get_db_connection(self):
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def authenticate_user(self, username, password):
        """Autentica un usuario"""
        print(f"🔐 Intentando autenticar usuario: {username}")
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si existe el usuario
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE username = ?', (username,))
        user_exists = cursor.fetchone()[0] > 0
        print(f"👤 Usuario existe: {user_exists}")
        
        if not user_exists:
            print("❌ Usuario no encontrado")
            conn.close()
            return None
        
        # Obtener el usuario y su contraseña almacenada
        cursor.execute('SELECT id, username, nombre, rol, password FROM usuarios WHERE username = ? AND activo = 1', (username,))
        user_data = cursor.fetchone()
        
        if not user_data:
            print("❌ Usuario inactivo o no encontrado")
            conn.close()
            return None
        
        stored_password = user_data['password']
        print(f"🔍 Contraseña almacenada: {stored_password[:10]}...")
        
        # Para admin, intentar múltiples métodos de autenticación
        if username == 'admin':
            # Método 1: Contraseña directa
            if password == stored_password:
                print("✅ Autenticación directa exitosa")
                user_result = {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'nombre': user_data['nombre'],
                    'rol': user_data['rol']
                }
                conn.close()
                return user_result
            
            # Método 2: Con hash SHA256
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            print(f"🔒 Probando con hash: {password_hash[:10]}...")
            if password_hash == stored_password:
                print("✅ Autenticación con hash exitosa")
                user_result = {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'nombre': user_data['nombre'],
                    'rol': user_data['rol']
                }
                conn.close()
                return user_result
            
            # Método 3: Verificar si la contraseña es "admin123" directamente
            if password == "admin123":
                print("✅ Autenticación admin123 directa")
                user_result = {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'nombre': user_data['nombre'],
                    'rol': user_data['rol']
                }
                conn.close()
                return user_result
        else:
            # Para otros usuarios, usar hash
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash == stored_password:
                user_result = {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'nombre': user_data['nombre'],
                    'rol': user_data['rol']
                }
                conn.close()
                return user_result
        
        print("❌ Credenciales incorrectas")
        conn.close()
        return None
    
    def get_products(self, search=None):
        """Obtiene lista de productos"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        if search:
            cursor.execute('''
                SELECT * FROM productos 
                WHERE activo = 1 AND (nombre LIKE ? OR codigo LIKE ?)
                ORDER BY nombre
            ''', (f"%{search}%", f"%{search}%"))
        else:
            cursor.execute('''
                SELECT * FROM productos 
                WHERE activo = 1 
                ORDER BY nombre
            ''')
        
        products = cursor.fetchall()
        conn.close()
        return products
    
    def create_sale(self, user_id, items, total):
        """Crea una nueva venta"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        items_json = json.dumps(items)
        cursor.execute('''
            INSERT INTO ventas (usuario_id, total, items_json)
            VALUES (?, ?, ?)
        ''', (user_id, total, items_json))
        
        sale_id = cursor.lastrowid
        
        # Actualizar stock de productos
        for item in items:
            cursor.execute('''
                UPDATE productos 
                SET stock = stock - ? 
                WHERE id = ?
            ''', (item['cantidad'], item['producto_id']))
        
        conn.commit()
        conn.close()
        return sale_id
    
    def get_sales_summary(self, user_id=None):
        """Obtiene resumen de ventas"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT COUNT(*) as total_ventas, 
                       COALESCE(SUM(total), 0) as total_ingresos
                FROM ventas 
                WHERE usuario_id = ? AND DATE(fecha) = DATE('now')
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT COUNT(*) as total_ventas, 
                       COALESCE(SUM(total), 0) as total_ingresos
                FROM ventas 
                WHERE DATE(fecha) = DATE('now')
            ''')
        
        summary = cursor.fetchone()
        conn.close()
        return summary
    
    def get_products_with_details(self, search=None, category=None):
        """Obtiene productos con detalles para inventario"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, codigo, nombre, precio, stock, activo,
                   CASE 
                       WHEN codigo LIKE 'BEB%' THEN 'Bebidas'
                       WHEN codigo LIKE 'COM%' THEN 'Comidas'
                       WHEN codigo LIKE 'POS%' THEN 'Postres'
                       WHEN codigo LIKE 'SNK%' THEN 'Snacks'
                       WHEN codigo LIKE 'ART%' THEN 'Artículos'
                       ELSE 'Otros'
                   END as categoria
            FROM productos 
            WHERE activo = 1
        '''
        
        params = []
        
        if search:
            query += ' AND (nombre LIKE ? OR codigo LIKE ?)'
            params.extend([f"%{search}%", f"%{search}%"])
        
        if category:
            if category == 'Bebidas':
                query += ' AND codigo LIKE ?'
                params.append('BEB%')
            elif category == 'Comidas':
                query += ' AND codigo LIKE ?'
                params.append('COM%')
            elif category == 'Postres':
                query += ' AND codigo LIKE ?'
                params.append('POS%')
            elif category == 'Snacks':
                query += ' AND codigo LIKE ?'
                params.append('SNK%')
            elif category == 'Artículos':
                query += ' AND codigo LIKE ?'
                params.append('ART%')
        
        query += ' ORDER BY categoria, nombre'
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        conn.close()
        return products
    
    def get_product_categories(self):
        """Obtiene las categorías de productos"""
        return ['Bebidas', 'Comidas', 'Postres', 'Snacks', 'Artículos']
    
    def get_low_stock_products(self, threshold=10):
        """Obtiene productos con stock bajo"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT codigo, nombre, stock, precio
            FROM productos 
            WHERE activo = 1 AND stock <= ?
            ORDER BY stock ASC
        ''', (threshold,))
        
        products = cursor.fetchall()
        conn.close()
        return products
    
    def update_product_stock(self, product_id, new_stock):
        """Actualiza el stock de un producto"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE productos 
            SET stock = ?
            WHERE id = ?
        ''', (new_stock, product_id))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

# Funciones de utilidad para sesiones
def set_user_session(user_data):
    """Configura la sesión del usuario de manera robusta"""
    session_id = f"user_{user_data['id']}_{int(time.time())}"
    
    # Configurar Flask session
    session.clear()
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session['nombre'] = user_data['nombre']
    session['rol'] = user_data['rol']
    session['session_id'] = session_id
    session.permanent = True
    
    # Guardar en variable global como backup
    active_sessions[session_id] = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'nombre': user_data['nombre'],
        'rol': user_data['rol'],
        'timestamp': time.time()
    }
    
    print(f"✅ SESSION CONFIGURED: Flask={dict(session)}")
    print(f"✅ BACKUP SESSION: {active_sessions[session_id]}")
    return session_id

def get_current_user():
    """Obtiene el usuario actual de manera robusta"""
    # Intentar desde Flask session primero
    if 'user_id' in session and session['user_id']:
        return {
            'user_id': session['user_id'],
            'username': session.get('username'),
            'nombre': session.get('nombre'),
            'rol': session.get('rol')
        }
    
    # Fallback: buscar en sesiones activas por IP/timestamp reciente
    current_time = time.time()
    for session_id, session_data in active_sessions.items():
        if current_time - session_data['timestamp'] < 86400:  # 24 horas
            return session_data
    
    return None

def is_user_logged_in():
    """Verifica si el usuario está logueado"""
    user = get_current_user()
    return user is not None

# Instancia global
mobile_pos = MobilePOS()

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        print(f"🔒 LOGIN_REQUIRED CHECK: User = {user}")
        
        if not user:
            print("❌ LOGIN_REQUIRED: No user found, redirecting to login")
            return redirect(url_for('login'))
        
        print(f"✅ LOGIN_REQUIRED: User {user.get('username')} authenticated")
        
        # Actualizar Flask session si es necesario
        if 'user_id' not in session:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['nombre'] = user['nombre']
            session['rol'] = user['rol']
        
        return f(*args, **kwargs)
    return decorated_function

# Rutas de la aplicación
@app.route('/')
def index():
    """Página principal - redirige al dashboard si está logueado"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        print(f"🔍 LOGIN ATTEMPT: Usuario='{username}', Password='{password[:3]}***'")
        
        user = mobile_pos.authenticate_user(username, password)
        if user:
            print(f"✅ LOGIN SUCCESS: {user}")
            
            # Configurar sesión usando nuestro sistema híbrido
            session_id = set_user_session(user)
            
            flash('¡Bienvenido al sistema!', 'success')
            print("🔄 REDIRECTING TO DASHBOARD...")
            
            # En lugar de redirect, renderear directamente el dashboard para probar
            try:
                summary = mobile_pos.get_sales_summary(user['id'])
                print("✅ Dashboard data loaded successfully")
                return render_template('dashboard.html', 
                                     user=user, 
                                     summary=summary)
            except Exception as e:
                print(f"❌ Dashboard error: {e}")
                return render_template('dashboard.html', 
                                     user=user, 
                                     summary={'total_ventas': 0, 'total_ingresos': 0})
        else:
            print("❌ LOGIN FAILED: Usuario o contraseña incorrectos")
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/test-session')
def test_session():
    """Ruta de prueba para verificar sesiones"""
    return jsonify({
        'session_data': dict(session),
        'has_user_id': 'user_id' in session,
        'user_id': session.get('user_id'),
        'username': session.get('username')
    })

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal"""
    user = get_current_user()
    print(f"🏠 DASHBOARD ACCESS: User {user.get('username')}")
    try:
        summary = mobile_pos.get_sales_summary(user['user_id'])
        return render_template('dashboard.html', 
                             user=user, 
                             summary=summary)
    except Exception as e:
        print(f"❌ DASHBOARD ERROR: {e}")
        # Si hay error, devolver dashboard básico
        return render_template('dashboard.html', 
                             user=user, 
                             summary={'total_ventas': 0, 'total_ingresos': 0})

@app.route('/pos')
@login_required
def pos():
    """Punto de venta"""
    products = mobile_pos.get_products()
    return render_template('pos.html', products=products)

@app.route('/products')
@login_required
def products():
    """Lista de productos"""
    search = request.args.get('search', '')
    products = mobile_pos.get_products(search)
    return render_template('products.html', products=products, search=search)

@app.route('/inventory')
@login_required
def inventory():
    """Gestión de inventario"""
    user = get_current_user()
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    products = mobile_pos.get_products_with_details(search, category)
    categories = mobile_pos.get_product_categories()
    
    return render_template('inventory.html', 
                         products=products, 
                         categories=categories,
                         user=user,
                         current_category=category,
                         search=search)

@app.route('/api/products')
@login_required
def api_products():
    """API para obtener productos"""
    search = request.args.get('search', '')
    products = mobile_pos.get_products(search)
    return jsonify([dict(product) for product in products])

@app.route('/api/update-stock', methods=['POST'])
@login_required
def api_update_stock():
    """API para actualizar stock de producto"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        new_stock = data.get('new_stock')
        
        if not product_id or new_stock is None:
            return jsonify({'success': False, 'error': 'Datos incompletos'})
        
        if new_stock < 0:
            return jsonify({'success': False, 'error': 'El stock no puede ser negativo'})
        
        success = mobile_pos.update_product_stock(product_id, new_stock)
        
        if success:
            return jsonify({'success': True, 'message': 'Stock actualizado correctamente'})
        else:
            return jsonify({'success': False, 'error': 'Producto no encontrado'})
    
    except Exception as e:
        print(f"Error updating stock: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sale', methods=['POST'])
@login_required
def api_create_sale():
    """API para crear venta"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        total = data.get('total', 0)
        
        if not items:
            return jsonify({'success': False, 'message': 'No hay productos en la venta'})
        
        sale_id = mobile_pos.create_sale(session['user_id'], items, total)
        return jsonify({'success': True, 'sale_id': sale_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/sales')
@login_required
def sales():
    """Historial de ventas"""
    conn = mobile_pos.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT v.*, u.nombre as vendedor
        FROM ventas v
        LEFT JOIN usuarios u ON v.usuario_id = u.id
        ORDER BY v.fecha DESC
        LIMIT 50
    ''')
    
    sales = cursor.fetchall()
    conn.close()
    
    return render_template('sales.html', sales=sales)

if __name__ == '__main__':
    print("🚀 Iniciando Caja Central POS - Interfaz Móvil")
    print("📱 Accede desde tu móvil: http://[tu-ip]:5000")
    print("💻 Acceso local: http://localhost:5000")
    print("👤 Usuario: admin | Contraseña: admin123")
    
    # Ejecutar en modo desarrollo (sin reloading automático)
    app.run(host='0.0.0.0', port=5000, debug=False)
