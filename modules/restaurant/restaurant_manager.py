"""
Sistema de Gestión de Restaurante
Manejo de mesas, cuentas activas, comandas y servicio de restaurante
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class TableStatus(Enum):
    AVAILABLE = "disponible"
    OCCUPIED = "ocupada"
    RESERVED = "reservada"
    CLEANING = "limpieza"
    OUT_OF_SERVICE = "fuera_servicio"

class OrderStatus(Enum):
    PENDING = "pendiente"
    PREPARING = "preparando"
    READY = "listo"
    SERVED = "servido"
    CANCELLED = "cancelado"

@dataclass
class Table:
    id: str
    number: int
    name: str
    seats: int
    area: str  # 'salon', 'terraza', 'bar', 'privado'
    status: TableStatus
    waiter_id: Optional[str] = None
    waiter_name: Optional[str] = None
    current_account_id: Optional[str] = None
    last_occupied: Optional[datetime] = None
    notes: Optional[str] = None

@dataclass
class MenuItem:
    id: str
    code: str
    name: str
    description: str
    category: str  # 'entradas', 'platos_fuertes', 'bebidas', 'postres'
    price: float
    preparation_time: int  # minutos
    is_available: bool = True
    allergens: List[str] = None
    ingredients: List[str] = None

@dataclass
class OrderItem:
    id: str
    menu_item_id: str
    menu_item_name: str
    quantity: int
    unit_price: float
    modifications: List[str] = None
    status: OrderStatus = OrderStatus.PENDING
    preparation_notes: Optional[str] = None
    ordered_at: Optional[datetime] = None
    served_at: Optional[datetime] = None

@dataclass
class Account:
    id: str
    table_id: str
    table_number: int
    waiter_id: str
    waiter_name: str
    customer_count: int
    opened_at: datetime
    items: List[OrderItem]
    subtotal: float = 0.0
    tax_amount: float = 0.0
    service_charge: float = 0.0
    total_amount: float = 0.0
    status: str = "active"  # active, closed, cancelled
    notes: Optional[str] = None

class RestaurantManager:
    def __init__(self, db_path: str = "restaurant.db"):
        self.db_path = db_path
        self.init_database()
        self.load_default_data()
    
    def init_database(self):
        """Inicializar base de datos del restaurante"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de mesas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tables (
                id TEXT PRIMARY KEY,
                number INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                seats INTEGER NOT NULL,
                area TEXT NOT NULL,
                status TEXT DEFAULT 'disponible',
                waiter_id TEXT,
                waiter_name TEXT,
                current_account_id TEXT,
                last_occupied DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de menú
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                preparation_time INTEGER DEFAULT 15,
                is_available BOOLEAN DEFAULT 1,
                allergens TEXT, -- JSON array
                ingredients TEXT, -- JSON array
                image_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de cuentas activas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                table_id TEXT NOT NULL,
                table_number INTEGER NOT NULL,
                waiter_id TEXT NOT NULL,
                waiter_name TEXT NOT NULL,
                customer_count INTEGER DEFAULT 1,
                opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                closed_at DATETIME,
                subtotal REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                service_charge REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                payment_method TEXT,
                notes TEXT,
                FOREIGN KEY (table_id) REFERENCES tables (id)
            )
        ''')
        
        # Tabla de items de órdenes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                menu_item_id TEXT NOT NULL,
                menu_item_name TEXT NOT NULL,
                menu_item_code TEXT,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL,
                modifications TEXT, -- JSON array
                status TEXT DEFAULT 'pendiente',
                preparation_notes TEXT,
                ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                prepared_at DATETIME,
                served_at DATETIME,
                cancelled_at DATETIME,
                kitchen_notes TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
            )
        ''')
        
        # Tabla de reservaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                table_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                customer_email TEXT,
                party_size INTEGER NOT NULL,
                reservation_date DATE NOT NULL,
                reservation_time TIME NOT NULL,
                duration_minutes INTEGER DEFAULT 120,
                status TEXT DEFAULT 'confirmed', -- confirmed, cancelled, completed, no_show
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (table_id) REFERENCES tables (id)
            )
        ''')
        
        # Tabla de configuración del restaurante
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restaurant_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_status ON order_items (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tables_status ON tables (status)')
        
        conn.commit()
        conn.close()
    
    def load_default_data(self):
        """Cargar datos por defecto si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si hay mesas
        cursor.execute('SELECT COUNT(*) FROM tables')
        table_count = cursor.fetchone()[0]
        
        if table_count == 0:
            # Crear mesas por defecto
            default_tables = [
                # Salón principal
                {'number': 1, 'name': 'Mesa 1', 'seats': 4, 'area': 'salon'},
                {'number': 2, 'name': 'Mesa 2', 'seats': 2, 'area': 'salon'},
                {'number': 3, 'name': 'Mesa 3', 'seats': 6, 'area': 'salon'},
                {'number': 4, 'name': 'Mesa 4', 'seats': 4, 'area': 'salon'},
                {'number': 5, 'name': 'Mesa 5', 'seats': 4, 'area': 'salon'},
                {'number': 6, 'name': 'Mesa 6', 'seats': 8, 'area': 'salon'},
                
                # Terraza
                {'number': 11, 'name': 'Terraza 1', 'seats': 4, 'area': 'terraza'},
                {'number': 12, 'name': 'Terraza 2', 'seats': 6, 'area': 'terraza'},
                {'number': 13, 'name': 'Terraza 3', 'seats': 2, 'area': 'terraza'},
                
                # Barra
                {'number': 21, 'name': 'Barra 1', 'seats': 2, 'area': 'bar'},
                {'number': 22, 'name': 'Barra 2', 'seats': 2, 'area': 'bar'},
                {'number': 23, 'name': 'Barra 3', 'seats': 4, 'area': 'bar'},
                
                # Área privada
                {'number': 31, 'name': 'Privado VIP', 'seats': 10, 'area': 'privado'},
            ]
            
            for table_data in default_tables:
                table_id = f"table_{table_data['number']:03d}"
                cursor.execute('''
                    INSERT INTO tables (id, number, name, seats, area, status)
                    VALUES (?, ?, ?, ?, ?, 'disponible')
                ''', (table_id, table_data['number'], table_data['name'], 
                     table_data['seats'], table_data['area']))
        
        # Verificar si hay items de menú
        cursor.execute('SELECT COUNT(*) FROM menu_items')
        menu_count = cursor.fetchone()[0]
        
        if menu_count == 0:
            # Crear menú por defecto
            default_menu = [
                # Entradas
                {'code': 'ENT001', 'name': 'Nachos Supremos', 'description': 'Nachos con queso, frijoles, guacamole y crema', 'category': 'entradas', 'price': 4500, 'prep_time': 10},
                {'code': 'ENT002', 'name': 'Alitas BBQ', 'description': '8 alitas de pollo con salsa BBQ', 'category': 'entradas', 'price': 5200, 'prep_time': 15},
                {'code': 'ENT003', 'name': 'Quesadillas', 'description': 'Tortillas con queso y pollo', 'category': 'entradas', 'price': 3800, 'prep_time': 8},
                
                # Platos Fuertes
                {'code': 'PLT001', 'name': 'Casado Tradicional', 'description': 'Arroz, frijoles, carne, plátano, ensalada', 'category': 'platos_fuertes', 'price': 6500, 'prep_time': 20},
                {'code': 'PLT002', 'name': 'Pollo a la Plancha', 'description': 'Pechuga con vegetales y papas', 'category': 'platos_fuertes', 'price': 7200, 'prep_time': 25},
                {'code': 'PLT003', 'name': 'Pescado del Día', 'description': 'Filete de pescado con arroz y ensalada', 'category': 'platos_fuertes', 'price': 8500, 'prep_time': 30},
                {'code': 'PLT004', 'name': 'Hamburguesa Gourmet', 'description': 'Carne artesanal con papas fritas', 'category': 'platos_fuertes', 'price': 5800, 'prep_time': 18},
                
                # Bebidas
                {'code': 'BEB001', 'name': 'Refresco Natural', 'description': 'Frescos de frutas naturales', 'category': 'bebidas', 'price': 1200, 'prep_time': 3},
                {'code': 'BEB002', 'name': 'Cerveza Nacional', 'description': 'Cerveza fría nacional', 'category': 'bebidas', 'price': 1500, 'prep_time': 1},
                {'code': 'BEB003', 'name': 'Café Americano', 'description': 'Café negro recién hecho', 'category': 'bebidas', 'price': 800, 'prep_time': 3},
                {'code': 'BEB004', 'name': 'Batido de Frutas', 'description': 'Batido natural con leche', 'category': 'bebidas', 'price': 2200, 'prep_time': 5},
                
                # Postres
                {'code': 'POS001', 'name': 'Tres Leches', 'description': 'Pastel tres leches casero', 'category': 'postres', 'price': 2800, 'prep_time': 5},
                {'code': 'POS002', 'name': 'Flan de Coco', 'description': 'Flan cremoso de coco', 'category': 'postres', 'price': 2400, 'prep_time': 3},
                {'code': 'POS003', 'name': 'Helado Artesanal', 'description': '2 bolas de helado con topping', 'category': 'postres', 'price': 2000, 'prep_time': 2},
            ]
            
            for item in default_menu:
                item_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO menu_items 
                    (id, code, name, description, category, price, preparation_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (item_id, item['code'], item['name'], item['description'],
                     item['category'], item['price'], item['prep_time']))
        
        # Configuración por defecto
        cursor.execute('SELECT COUNT(*) FROM restaurant_config')
        config_count = cursor.fetchone()[0]
        
        if config_count == 0:
            default_config = [
                ('restaurant_name', 'Restaurante Caja Central', 'Nombre del restaurante'),
                ('tax_rate', '13.0', 'Porcentaje de IVA'),
                ('service_charge_rate', '10.0', 'Porcentaje de servicio'),
                ('default_reservation_duration', '120', 'Duración por defecto de reservaciones en minutos'),
                ('kitchen_printer_enabled', 'true', 'Habilitar impresora de cocina'),
                ('auto_service_charge', 'true', 'Aplicar cargo por servicio automáticamente'),
            ]
            
            for key, value, description in default_config:
                cursor.execute('''
                    INSERT INTO restaurant_config (key, value, description)
                    VALUES (?, ?, ?)
                ''', (key, value, description))
        
        conn.commit()
        conn.close()
    
    def get_all_tables(self) -> List[Table]:
        """Obtener todas las mesas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, number, name, seats, area, status, waiter_id, waiter_name,
                   current_account_id, last_occupied, notes
            FROM tables
            ORDER BY area, number
        ''')
        
        tables = []
        for row in cursor.fetchall():
            tables.append(Table(
                id=row[0],
                number=row[1],
                name=row[2],
                seats=row[3],
                area=row[4],
                status=TableStatus(row[5]),
                waiter_id=row[6],
                waiter_name=row[7],
                current_account_id=row[8],
                last_occupied=datetime.fromisoformat(row[9]) if row[9] else None,
                notes=row[10]
            ))
        
        conn.close()
        return tables
    
    def get_tables_by_area(self, area: str) -> List[Table]:
        """Obtener mesas por área"""
        tables = self.get_all_tables()
        return [table for table in tables if table.area == area]
    
    def update_table_status(self, table_id: str, status: TableStatus, 
                           waiter_id: str = None, waiter_name: str = None):
        """Actualizar estado de mesa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ['status = ?']
        params = [status.value]
        
        if waiter_id:
            update_fields.append('waiter_id = ?')
            params.append(waiter_id)
        
        if waiter_name:
            update_fields.append('waiter_name = ?')
            params.append(waiter_name)
        
        if status == TableStatus.OCCUPIED:
            update_fields.append('last_occupied = CURRENT_TIMESTAMP')
        
        params.append(table_id)
        
        cursor.execute(f'''
            UPDATE tables 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)
        
        conn.commit()
        conn.close()
    
    def create_account(self, table_id: str, waiter_id: str, waiter_name: str, 
                      customer_count: int = 1, notes: str = "") -> str:
        """Crear nueva cuenta para mesa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            conn.execute('BEGIN TRANSACTION')
            
            # Verificar que la mesa esté disponible
            cursor.execute('SELECT status FROM tables WHERE id = ?', (table_id,))
            table_status = cursor.fetchone()
            
            if not table_status or table_status[0] != 'disponible':
                raise ValueError("Mesa no disponible")
            
            # Crear cuenta
            account_id = str(uuid.uuid4())
            cursor.execute('SELECT number FROM tables WHERE id = ?', (table_id,))
            table_number = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO accounts 
                (id, table_id, table_number, waiter_id, waiter_name, customer_count, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, table_id, table_number, waiter_id, waiter_name, customer_count, notes))
            
            # Actualizar estado de mesa
            cursor.execute('''
                UPDATE tables 
                SET status = 'ocupada', waiter_id = ?, waiter_name = ?, 
                    current_account_id = ?, last_occupied = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (waiter_id, waiter_name, account_id, table_id))
            
            conn.commit()
            return account_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def add_items_to_account(self, account_id: str, items: List[Dict]) -> List[str]:
        """Agregar items a una cuenta"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            conn.execute('BEGIN TRANSACTION')
            
            item_ids = []
            account_total = 0
            
            for item in items:
                # Obtener información del item del menú
                cursor.execute('''
                    SELECT id, name, code, price FROM menu_items 
                    WHERE id = ? AND is_available = 1
                ''', (item['menu_item_id'],))
                
                menu_item = cursor.fetchone()
                if not menu_item:
                    raise ValueError(f"Item de menú no encontrado: {item['menu_item_id']}")
                
                # Crear item de orden
                item_id = str(uuid.uuid4())
                quantity = item.get('quantity', 1)
                unit_price = menu_item[3]
                line_total = quantity * unit_price
                
                cursor.execute('''
                    INSERT INTO order_items 
                    (id, account_id, menu_item_id, menu_item_name, menu_item_code,
                     quantity, unit_price, line_total, modifications, preparation_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_id, account_id, menu_item[0], menu_item[1], menu_item[2],
                    quantity, unit_price, line_total,
                    json.dumps(item.get('modifications', [])),
                    item.get('preparation_notes', '')
                ))
                
                item_ids.append(item_id)
                account_total += line_total
            
            # Actualizar totales de la cuenta
            self._update_account_totals(cursor, account_id)
            
            conn.commit()
            return item_ids
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _update_account_totals(self, cursor, account_id: str):
        """Actualizar totales de una cuenta"""
        # Calcular subtotal
        cursor.execute('''
            SELECT SUM(line_total) FROM order_items 
            WHERE account_id = ? AND status != 'cancelado'
        ''', (account_id,))
        
        subtotal = cursor.fetchone()[0] or 0
        
        # Obtener configuración de impuestos
        cursor.execute('SELECT value FROM restaurant_config WHERE key = ?', ('tax_rate',))
        tax_rate = float(cursor.fetchone()[0] or 13.0) / 100
        
        cursor.execute('SELECT value FROM restaurant_config WHERE key = ?', ('service_charge_rate',))
        service_rate = float(cursor.fetchone()[0] or 10.0) / 100
        
        cursor.execute('SELECT value FROM restaurant_config WHERE key = ?', ('auto_service_charge',))
        auto_service = cursor.fetchone()[0] or 'true'
        
        # Calcular impuestos y servicio
        tax_amount = subtotal * tax_rate
        service_charge = subtotal * service_rate if auto_service.lower() == 'true' else 0
        total_amount = subtotal + tax_amount + service_charge
        
        # Actualizar cuenta
        cursor.execute('''
            UPDATE accounts 
            SET subtotal = ?, tax_amount = ?, service_charge = ?, total_amount = ?
            WHERE id = ?
        ''', (subtotal, tax_amount, service_charge, total_amount, account_id))
    
    def get_active_accounts(self) -> List[Account]:
        """Obtener todas las cuentas activas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, table_id, table_number, waiter_id, waiter_name, customer_count,
                   opened_at, subtotal, tax_amount, service_charge, total_amount, status, notes
            FROM accounts
            WHERE status = 'active'
            ORDER BY opened_at
        ''')
        
        accounts = []
        for row in cursor.fetchall():
            account_id = row[0]
            
            # Obtener items de la cuenta
            cursor.execute('''
                SELECT id, menu_item_id, menu_item_name, quantity, unit_price,
                       modifications, status, preparation_notes, ordered_at, served_at
                FROM order_items
                WHERE account_id = ?
                ORDER BY ordered_at
            ''', (account_id,))
            
            items = []
            for item_row in cursor.fetchall():
                items.append(OrderItem(
                    id=item_row[0],
                    menu_item_id=item_row[1],
                    menu_item_name=item_row[2],
                    quantity=item_row[3],
                    unit_price=item_row[4],
                    modifications=json.loads(item_row[5]) if item_row[5] else [],
                    status=OrderStatus(item_row[6]),
                    preparation_notes=item_row[7],
                    ordered_at=datetime.fromisoformat(item_row[8]) if item_row[8] else None,
                    served_at=datetime.fromisoformat(item_row[9]) if item_row[9] else None
                ))
            
            accounts.append(Account(
                id=account_id,
                table_id=row[1],
                table_number=row[2],
                waiter_id=row[3],
                waiter_name=row[4],
                customer_count=row[5],
                opened_at=datetime.fromisoformat(row[6]),
                items=items,
                subtotal=row[7],
                tax_amount=row[8],
                service_charge=row[9],
                total_amount=row[10],
                status=row[11],
                notes=row[12]
            ))
        
        conn.close()
        return accounts
    
    def get_account_by_table(self, table_id: str) -> Optional[Account]:
        """Obtener cuenta activa de una mesa"""
        accounts = self.get_active_accounts()
        for account in accounts:
            if account.table_id == table_id:
                return account
        return None
    
    def update_item_status(self, item_id: str, status: OrderStatus):
        """Actualizar estado de un item de orden"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ['status = ?']
        params = [status.value]
        
        if status == OrderStatus.READY:
            update_fields.append('prepared_at = CURRENT_TIMESTAMP')
        elif status == OrderStatus.SERVED:
            update_fields.append('served_at = CURRENT_TIMESTAMP')
        elif status == OrderStatus.CANCELLED:
            update_fields.append('cancelled_at = CURRENT_TIMESTAMP')
        
        params.append(item_id)
        
        cursor.execute(f'''
            UPDATE order_items 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)
        
        conn.commit()
        conn.close()
    
    def close_account(self, account_id: str, payment_method: str = "efectivo") -> Dict:
        """Cerrar cuenta y liberar mesa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            conn.execute('BEGIN TRANSACTION')
            
            # Obtener información de la cuenta
            cursor.execute('''
                SELECT table_id, total_amount FROM accounts 
                WHERE id = ? AND status = 'active'
            ''', (account_id,))
            
            account_info = cursor.fetchone()
            if not account_info:
                raise ValueError("Cuenta no encontrada o ya cerrada")
            
            table_id, total_amount = account_info
            
            # Cerrar cuenta
            cursor.execute('''
                UPDATE accounts 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP, payment_method = ?
                WHERE id = ?
            ''', (payment_method, account_id))
            
            # Liberar mesa
            cursor.execute('''
                UPDATE tables 
                SET status = 'disponible', waiter_id = NULL, waiter_name = NULL, current_account_id = NULL
                WHERE id = ?
            ''', (table_id,))
            
            # Marcar todos los items como servidos si no lo están
            cursor.execute('''
                UPDATE order_items 
                SET status = 'servido', served_at = CURRENT_TIMESTAMP
                WHERE account_id = ? AND status != 'cancelado'
            ''', (account_id,))
            
            conn.commit()
            
            return {
                'success': True,
                'account_id': account_id,
                'total_amount': total_amount,
                'payment_method': payment_method
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def get_menu_by_category(self) -> Dict[str, List[MenuItem]]:
        """Obtener menú organizado por categorías"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, code, name, description, category, price, preparation_time,
                   is_available, allergens, ingredients
            FROM menu_items
            WHERE is_available = 1
            ORDER BY category, name
        ''')
        
        menu = {}
        for row in cursor.fetchall():
            category = row[4]
            if category not in menu:
                menu[category] = []
            
            menu[category].append(MenuItem(
                id=row[0],
                code=row[1],
                name=row[2],
                description=row[3],
                category=row[4],
                price=row[5],
                preparation_time=row[6],
                is_available=bool(row[7]),
                allergens=json.loads(row[8]) if row[8] else [],
                ingredients=json.loads(row[9]) if row[9] else []
            ))
        
        conn.close()
        return menu
    
    def get_kitchen_orders(self) -> List[Dict]:
        """Obtener órdenes para cocina"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT oi.id, oi.menu_item_name, oi.quantity, oi.modifications,
                   oi.preparation_notes, oi.ordered_at, oi.status,
                   a.table_number, a.waiter_name, mi.preparation_time
            FROM order_items oi
            JOIN accounts a ON oi.account_id = a.id
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.status IN ('pendiente', 'preparando')
            AND a.status = 'active'
            ORDER BY oi.ordered_at
        ''')
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0],
                'item_name': row[1],
                'quantity': row[2],
                'modifications': json.loads(row[3]) if row[3] else [],
                'preparation_notes': row[4],
                'ordered_at': row[5],
                'status': row[6],
                'table_number': row[7],
                'waiter_name': row[8],
                'preparation_time': row[9]
            })
        
        conn.close()
        return orders
    
    def get_restaurant_stats(self) -> Dict:
        """Obtener estadísticas del restaurante"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estadísticas de mesas
        cursor.execute('''
            SELECT status, COUNT(*) FROM tables GROUP BY status
        ''')
        table_stats = dict(cursor.fetchall())
        
        # Cuentas activas
        cursor.execute('SELECT COUNT(*) FROM accounts WHERE status = "active"')
        active_accounts = cursor.fetchone()[0]
        
        # Ingresos del día
        today = datetime.now().date()
        cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0) 
            FROM accounts 
            WHERE DATE(closed_at) = ? AND status = 'closed'
        ''', (today,))
        
        daily_stats = cursor.fetchone()
        
        # Items pendientes en cocina
        cursor.execute('''
            SELECT COUNT(*) FROM order_items oi
            JOIN accounts a ON oi.account_id = a.id
            WHERE oi.status IN ('pendiente', 'preparando') AND a.status = 'active'
        ''')
        pending_kitchen = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'tables': {
                'total': sum(table_stats.values()),
                'available': table_stats.get('disponible', 0),
                'occupied': table_stats.get('ocupada', 0),
                'reserved': table_stats.get('reservada', 0),
                'cleaning': table_stats.get('limpieza', 0),
                'out_of_service': table_stats.get('fuera_servicio', 0)
            },
            'accounts': {
                'active': active_accounts
            },
            'daily': {
                'transactions': daily_stats[0],
                'revenue': daily_stats[1]
            },
            'kitchen': {
                'pending_items': pending_kitchen
            }
        }
