"""
Sistema de Gestión Multi-Tienda
Manejo de inventario y sincronización entre múltiples sucursales
"""

import sqlite3
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time
from dataclasses import dataclass
import uuid

@dataclass
class Store:
    id: str
    name: str
    address: str
    manager: str
    phone: str
    email: str
    is_active: bool
    sync_enabled: bool
    last_sync: datetime = None

@dataclass
class StockMovement:
    id: str
    store_id: str
    product_code: str
    movement_type: str  # 'sale', 'purchase', 'transfer', 'adjustment'
    quantity: int
    reference: str
    timestamp: datetime
    user_id: str

class MultiStoreManager:
    def __init__(self, config_path: str = "config/multistore_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.db_path = "multistore_data.db"
        self.init_database()
        self.sync_thread = None
        self.sync_active = False
        
    def load_config(self) -> Dict:
        """Cargar configuración multi-tienda"""
        default_config = {
            "current_store_id": "store001",
            "sync_interval": 300,  # 5 minutos
            "central_server": {
                "enabled": False,
                "url": "https://api.cajacentral.com",
                "api_key": ""
            },
            "stores": [
                {
                    "id": "store001",
                    "name": "Sucursal Principal",
                    "address": "San José Centro",
                    "manager": "Admin Principal",
                    "phone": "2222-3333",
                    "email": "principal@empresa.com",
                    "is_active": True,
                    "sync_enabled": True
                }
            ]
        }
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict):
        """Guardar configuración"""
        import os
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def init_database(self):
        """Inicializar base de datos multi-tienda"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de tiendas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stores (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                manager TEXT,
                phone TEXT,
                email TEXT,
                is_active BOOLEAN DEFAULT 1,
                sync_enabled BOOLEAN DEFAULT 1,
                last_sync DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de stock por tienda
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS store_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT,
                product_code TEXT,
                current_stock INTEGER DEFAULT 0,
                reserved_stock INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 0,
                max_stock INTEGER DEFAULT 1000,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores (id),
                UNIQUE(store_id, product_code)
            )
        ''')
        
        # Tabla de movimientos de stock
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id TEXT PRIMARY KEY,
                store_id TEXT,
                product_code TEXT,
                movement_type TEXT,
                quantity INTEGER,
                previous_stock INTEGER,
                new_stock INTEGER,
                reference TEXT,
                notes TEXT,
                user_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT 0,
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        ''')
        
        # Tabla de transferencias entre tiendas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS store_transfers (
                id TEXT PRIMARY KEY,
                from_store_id TEXT,
                to_store_id TEXT,
                product_code TEXT,
                quantity INTEGER,
                status TEXT DEFAULT 'pending', -- pending, in_transit, completed, cancelled
                requested_by TEXT,
                approved_by TEXT,
                completed_by TEXT,
                request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                completion_date DATETIME,
                notes TEXT,
                FOREIGN KEY (from_store_id) REFERENCES stores (id),
                FOREIGN KEY (to_store_id) REFERENCES stores (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insertar tienda actual si no existe
        self.register_current_store()
    
    def register_current_store(self):
        """Registrar la tienda actual en la base de datos"""
        current_store = next(
            (s for s in self.config['stores'] if s['id'] == self.config['current_store_id']),
            None
        )
        
        if current_store:
            self.add_or_update_store(Store(**current_store))
    
    def add_or_update_store(self, store: Store):
        """Agregar o actualizar información de tienda"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO stores 
            (id, name, address, manager, phone, email, is_active, sync_enabled, last_sync)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            store.id, store.name, store.address, store.manager,
            store.phone, store.email, store.is_active, store.sync_enabled,
            store.last_sync
        ))
        
        conn.commit()
        conn.close()
    
    def get_store_stock(self, store_id: str, product_code: str = None) -> List[Dict]:
        """Obtener stock de una tienda específica"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if product_code:
            cursor.execute('''
                SELECT si.*, s.name as store_name
                FROM store_inventory si
                JOIN stores s ON si.store_id = s.id
                WHERE si.store_id = ? AND si.product_code = ?
            ''', (store_id, product_code))
        else:
            cursor.execute('''
                SELECT si.*, s.name as store_name
                FROM store_inventory si
                JOIN stores s ON si.store_id = s.id
                WHERE si.store_id = ?
                ORDER BY si.product_code
            ''', (store_id,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_consolidated_stock(self, product_code: str) -> List[Dict]:
        """Obtener stock consolidado de todas las tiendas para un producto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                si.store_id,
                s.name as store_name,
                si.product_code,
                si.current_stock,
                si.reserved_stock,
                si.min_stock,
                si.max_stock,
                si.last_updated,
                s.is_active
            FROM store_inventory si
            JOIN stores s ON si.store_id = s.id
            WHERE si.product_code = ? AND s.is_active = 1
            ORDER BY s.name
        ''', (product_code,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def update_stock(self, store_id: str, product_code: str, quantity: int, 
                    movement_type: str, reference: str = "", user_id: str = "system"):
        """Actualizar stock y registrar movimiento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            conn.execute('BEGIN TRANSACTION')
            
            # Obtener stock actual
            cursor.execute('''
                SELECT current_stock FROM store_inventory 
                WHERE store_id = ? AND product_code = ?
            ''', (store_id, product_code))
            
            result = cursor.fetchone()
            previous_stock = result[0] if result else 0
            new_stock = previous_stock + quantity
            
            # Validar que no quede stock negativo
            if new_stock < 0 and movement_type in ['sale', 'transfer_out']:
                raise ValueError(f"Stock insuficiente. Stock actual: {previous_stock}, Cantidad solicitada: {abs(quantity)}")
            
            # Actualizar o insertar stock
            cursor.execute('''
                INSERT OR REPLACE INTO store_inventory 
                (store_id, product_code, current_stock, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (store_id, product_code, max(0, new_stock)))
            
            # Registrar movimiento
            movement_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO stock_movements 
                (id, store_id, product_code, movement_type, quantity, 
                 previous_stock, new_stock, reference, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                movement_id, store_id, product_code, movement_type,
                quantity, previous_stock, new_stock, reference, user_id
            ))
            
            conn.commit()
            return {
                'success': True,
                'movement_id': movement_id,
                'previous_stock': previous_stock,
                'new_stock': new_stock
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def request_transfer(self, from_store_id: str, to_store_id: str, 
                        product_code: str, quantity: int, requested_by: str, notes: str = ""):
        """Solicitar transferencia entre tiendas"""
        transfer_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO store_transfers 
            (id, from_store_id, to_store_id, product_code, quantity, 
             requested_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            transfer_id, from_store_id, to_store_id, product_code,
            quantity, requested_by, notes
        ))
        
        conn.commit()
        conn.close()
        
        return transfer_id
    
    def approve_transfer(self, transfer_id: str, approved_by: str):
        """Aprobar transferencia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            conn.execute('BEGIN TRANSACTION')
            
            # Obtener datos de la transferencia
            cursor.execute('''
                SELECT from_store_id, to_store_id, product_code, quantity
                FROM store_transfers 
                WHERE id = ? AND status = 'pending'
            ''', (transfer_id,))
            
            transfer = cursor.fetchone()
            if not transfer:
                raise ValueError("Transferencia no encontrada o ya procesada")
            
            from_store, to_store, product_code, quantity = transfer
            
            # Verificar stock disponible
            cursor.execute('''
                SELECT current_stock FROM store_inventory 
                WHERE store_id = ? AND product_code = ?
            ''', (from_store, product_code))
            
            stock_result = cursor.fetchone()
            current_stock = stock_result[0] if stock_result else 0
            
            if current_stock < quantity:
                raise ValueError(f"Stock insuficiente en tienda origen. Disponible: {current_stock}")
            
            # Actualizar estado de transferencia
            cursor.execute('''
                UPDATE store_transfers 
                SET status = 'in_transit', approved_by = ?
                WHERE id = ?
            ''', (approved_by, transfer_id))
            
            # Reducir stock en tienda origen
            self.update_stock(from_store, product_code, -quantity, 'transfer_out', transfer_id)
            
            # Aumentar stock en tienda destino
            self.update_stock(to_store, product_code, quantity, 'transfer_in', transfer_id)
            
            # Completar transferencia
            cursor.execute('''
                UPDATE store_transfers 
                SET status = 'completed', completed_by = ?, completion_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (approved_by, transfer_id))
            
            conn.commit()
            return {'success': True, 'transfer_id': transfer_id}
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_pending_transfers(self, store_id: str = None) -> List[Dict]:
        """Obtener transferencias pendientes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if store_id:
            cursor.execute('''
                SELECT t.*, 
                       s1.name as from_store_name,
                       s2.name as to_store_name
                FROM store_transfers t
                JOIN stores s1 ON t.from_store_id = s1.id
                JOIN stores s2 ON t.to_store_id = s2.id
                WHERE (t.from_store_id = ? OR t.to_store_id = ?) 
                AND t.status IN ('pending', 'in_transit')
                ORDER BY t.request_date DESC
            ''', (store_id, store_id))
        else:
            cursor.execute('''
                SELECT t.*, 
                       s1.name as from_store_name,
                       s2.name as to_store_name
                FROM store_transfers t
                JOIN stores s1 ON t.from_store_id = s1.id
                JOIN stores s2 ON t.to_store_id = s2.id
                WHERE t.status IN ('pending', 'in_transit')
                ORDER BY t.request_date DESC
            ''')
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def start_sync(self):
        """Iniciar sincronización automática"""
        if self.sync_thread and self.sync_thread.is_alive():
            return
        
        self.sync_active = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
    
    def stop_sync(self):
        """Detener sincronización"""
        self.sync_active = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
    
    def _sync_loop(self):
        """Loop de sincronización"""
        while self.sync_active:
            try:
                self.sync_with_stores()
                time.sleep(self.config.get('sync_interval', 300))
            except Exception as e:
                print(f"Error en sincronización: {e}")
                time.sleep(60)  # Esperar 1 minuto en caso de error
    
    def sync_with_stores(self):
        """Sincronizar con otras tiendas"""
        if not self.config.get('central_server', {}).get('enabled'):
            return
        
        # Implementar sincronización con servidor central
        # Esta es una implementación básica
        try:
            # Enviar movimientos no sincronizados
            self._send_pending_movements()
            
            # Recibir movimientos de otras tiendas
            self._receive_movements()
            
        except Exception as e:
            print(f"Error sincronizando: {e}")
    
    def _send_pending_movements(self):
        """Enviar movimientos pendientes al servidor central"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM stock_movements 
            WHERE synced = 0 
            ORDER BY timestamp
        ''')
        
        pending_movements = cursor.fetchall()
        
        for movement in pending_movements:
            # Simular envío al servidor
            # En producción aquí iría la llamada HTTP al servidor central
            print(f"Sincronizando movimiento: {movement[0]}")
            
            # Marcar como sincronizado
            cursor.execute('''
                UPDATE stock_movements 
                SET synced = 1 
                WHERE id = ?
            ''', (movement[0],))
        
        conn.commit()
        conn.close()
    
    def _receive_movements(self):
        """Recibir movimientos de otras tiendas"""
        # Implementar recepción desde servidor central
        pass
    
    def get_store_performance(self, store_id: str, days: int = 30) -> Dict:
        """Obtener rendimiento de tienda"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener movimientos de venta de los últimos días
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sales,
                SUM(ABS(quantity)) as total_items_sold,
                DATE(timestamp) as sale_date
            FROM stock_movements 
            WHERE store_id = ? 
            AND movement_type = 'sale'
            AND timestamp >= datetime('now', '-{} days')
            GROUP BY DATE(timestamp)
            ORDER BY sale_date DESC
        '''.format(days), (store_id,))
        
        daily_sales = cursor.fetchall()
        
        # Total productos únicos
        cursor.execute('''
            SELECT COUNT(DISTINCT product_code) as unique_products
            FROM store_inventory 
            WHERE store_id = ? AND current_stock > 0
        ''', (store_id,))
        
        unique_products = cursor.fetchone()[0]
        
        # Productos con stock bajo
        cursor.execute('''
            SELECT COUNT(*) as low_stock_count
            FROM store_inventory 
            WHERE store_id = ? AND current_stock <= min_stock AND min_stock > 0
        ''', (store_id,))
        
        low_stock = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'daily_sales': daily_sales,
            'unique_products': unique_products,
            'low_stock_count': low_stock,
            'performance_period': days
        }
