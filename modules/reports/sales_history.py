"""
Sistema de Historial de Ventas y Reportes para Administradores
Funcionalidad completa de seguimiento y análisis de ventas
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64

@dataclass
class SaleRecord:
    id: str
    store_id: str
    store_name: str
    cashier_id: str
    cashier_name: str
    customer_id: Optional[str]
    customer_name: Optional[str]
    sale_date: datetime
    total_amount: float
    tax_amount: float
    discount_amount: float
    payment_method: str
    items_count: int
    status: str  # 'completed', 'cancelled', 'refunded'

@dataclass
class SaleItem:
    sale_id: str
    product_code: str
    product_name: str
    quantity: int
    unit_price: float
    discount_percentage: float
    tax_percentage: float
    line_total: float

class SalesHistoryManager:
    def __init__(self, db_path: str = "sales_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos de historial de ventas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de ventas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id TEXT PRIMARY KEY,
                store_id TEXT NOT NULL,
                store_name TEXT,
                cashier_id TEXT NOT NULL,
                cashier_name TEXT,
                customer_id TEXT,
                customer_name TEXT,
                sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                tax_amount REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                payment_method TEXT DEFAULT 'efectivo',
                items_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'completed',
                receipt_number TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de items de venta
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id TEXT NOT NULL,
                product_code TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount_percentage REAL DEFAULT 0,
                tax_percentage REAL DEFAULT 13,
                line_total REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales (id)
            )
        ''')
        
        # Tabla de resumen diario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT NOT NULL,
                summary_date DATE NOT NULL,
                total_sales REAL DEFAULT 0,
                total_transactions INTEGER DEFAULT 0,
                total_items INTEGER DEFAULT 0,
                total_tax REAL DEFAULT 0,
                total_discounts REAL DEFAULT 0,
                cash_sales REAL DEFAULT 0,
                card_sales REAL DEFAULT 0,
                other_sales REAL DEFAULT 0,
                refunds REAL DEFAULT 0,
                average_ticket REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(store_id, summary_date)
            )
        ''')
        
        # Tabla de productos más vendidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_sales_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT NOT NULL,
                product_code TEXT NOT NULL,
                product_name TEXT NOT NULL,
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                total_quantity INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0,
                transaction_count INTEGER DEFAULT 0,
                average_price REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para mejorar rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_date ON sales (sale_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_store ON sales (store_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_cashier ON sales (cashier_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items (sale_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items (product_code)')
        
        conn.commit()
        conn.close()
    
    def record_sale(self, sale_data: Dict) -> str:
        """Registrar una nueva venta"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            conn.execute('BEGIN TRANSACTION')
            
            sale_id = sale_data.get('id', f"SALE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(sale_data)) % 10000}")
            
            # Insertar venta principal
            cursor.execute('''
                INSERT OR REPLACE INTO sales 
                (id, store_id, store_name, cashier_id, cashier_name, customer_id, customer_name,
                 sale_date, total_amount, tax_amount, discount_amount, payment_method, 
                 items_count, status, receipt_number, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sale_id,
                sale_data.get('store_id', 'store001'),
                sale_data.get('store_name', 'Sucursal Principal'),
                sale_data.get('cashier_id', 'user001'),
                sale_data.get('cashier_name', 'Cajero'),
                sale_data.get('customer_id'),
                sale_data.get('customer_name'),
                sale_data.get('sale_date', datetime.now()),
                sale_data.get('total_amount', 0),
                sale_data.get('tax_amount', 0),
                sale_data.get('discount_amount', 0),
                sale_data.get('payment_method', 'efectivo'),
                len(sale_data.get('items', [])),
                sale_data.get('status', 'completed'),
                sale_data.get('receipt_number'),
                sale_data.get('notes')
            ))
            
            # Insertar items de la venta
            for item in sale_data.get('items', []):
                cursor.execute('''
                    INSERT INTO sale_items 
                    (sale_id, product_code, product_name, quantity, unit_price, 
                     discount_percentage, tax_percentage, line_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sale_id,
                    item.get('product_code', ''),
                    item.get('product_name', ''),
                    item.get('quantity', 1),
                    item.get('unit_price', 0),
                    item.get('discount_percentage', 0),
                    item.get('tax_percentage', 13),
                    item.get('line_total', 0)
                ))
            
            # Actualizar resumen diario
            self._update_daily_summary(cursor, sale_data)
            
            conn.commit()
            return sale_id
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error registrando venta: {str(e)}")
        finally:
            conn.close()
    
    def _update_daily_summary(self, cursor, sale_data: Dict):
        """Actualizar resumen diario"""
        store_id = sale_data.get('store_id', 'store001')
        sale_date = sale_data.get('sale_date', datetime.now()).date()
        total_amount = sale_data.get('total_amount', 0)
        tax_amount = sale_data.get('tax_amount', 0)
        discount_amount = sale_data.get('discount_amount', 0)
        payment_method = sale_data.get('payment_method', 'efectivo')
        items_count = len(sale_data.get('items', []))
        
        # Obtener totales actuales
        cursor.execute('''
            SELECT total_sales, total_transactions, total_items, total_tax, total_discounts,
                   cash_sales, card_sales, other_sales
            FROM daily_summary 
            WHERE store_id = ? AND summary_date = ?
        ''', (store_id, sale_date))
        
        current = cursor.fetchone()
        
        if current:
            # Actualizar existente
            new_total_sales = current[0] + total_amount
            new_transactions = current[1] + 1
            new_items = current[2] + items_count
            new_tax = current[3] + tax_amount
            new_discounts = current[4] + discount_amount
            
            # Actualizar por método de pago
            cash_sales = current[5]
            card_sales = current[6]
            other_sales = current[7]
            
            if payment_method.lower() in ['efectivo', 'cash']:
                cash_sales += total_amount
            elif payment_method.lower() in ['tarjeta', 'card']:
                card_sales += total_amount
            else:
                other_sales += total_amount
            
            average_ticket = new_total_sales / new_transactions if new_transactions > 0 else 0
            
            cursor.execute('''
                UPDATE daily_summary 
                SET total_sales = ?, total_transactions = ?, total_items = ?,
                    total_tax = ?, total_discounts = ?, cash_sales = ?,
                    card_sales = ?, other_sales = ?, average_ticket = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE store_id = ? AND summary_date = ?
            ''', (
                new_total_sales, new_transactions, new_items, new_tax, new_discounts,
                cash_sales, card_sales, other_sales, average_ticket, store_id, sale_date
            ))
        else:
            # Crear nuevo registro
            cash_sales = total_amount if payment_method.lower() in ['efectivo', 'cash'] else 0
            card_sales = total_amount if payment_method.lower() in ['tarjeta', 'card'] else 0
            other_sales = total_amount if payment_method.lower() not in ['efectivo', 'cash', 'tarjeta', 'card'] else 0
            
            cursor.execute('''
                INSERT INTO daily_summary 
                (store_id, summary_date, total_sales, total_transactions, total_items,
                 total_tax, total_discounts, cash_sales, card_sales, other_sales, average_ticket)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                store_id, sale_date, total_amount, 1, items_count,
                tax_amount, discount_amount, cash_sales, card_sales, other_sales, total_amount
            ))
    
    def get_sales_history(self, 
                         store_id: str = None,
                         start_date: datetime = None,
                         end_date: datetime = None,
                         cashier_id: str = None,
                         customer_id: str = None,
                         payment_method: str = None,
                         status: str = None,
                         limit: int = 100,
                         offset: int = 0) -> List[SaleRecord]:
        """Obtener historial de ventas con filtros"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Construir query dinámicamente
        where_conditions = []
        params = []
        
        if store_id:
            where_conditions.append("store_id = ?")
            params.append(store_id)
        
        if start_date:
            where_conditions.append("sale_date >= ?")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("sale_date <= ?")
            params.append(end_date)
        
        if cashier_id:
            where_conditions.append("cashier_id = ?")
            params.append(cashier_id)
        
        if customer_id:
            where_conditions.append("customer_id = ?")
            params.append(customer_id)
        
        if payment_method:
            where_conditions.append("payment_method = ?")
            params.append(payment_method)
        
        if status:
            where_conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f'''
            SELECT id, store_id, store_name, cashier_id, cashier_name, 
                   customer_id, customer_name, sale_date, total_amount, 
                   tax_amount, discount_amount, payment_method, items_count, status
            FROM sales 
            WHERE {where_clause}
            ORDER BY sale_date DESC
            LIMIT ? OFFSET ?
        '''
        
        params.extend([limit, offset])
        cursor.execute(query, params)
        
        sales = []
        for row in cursor.fetchall():
            sales.append(SaleRecord(
                id=row[0],
                store_id=row[1],
                store_name=row[2],
                cashier_id=row[3],
                cashier_name=row[4],
                customer_id=row[5],
                customer_name=row[6],
                sale_date=datetime.fromisoformat(row[7]) if row[7] else None,
                total_amount=row[8],
                tax_amount=row[9],
                discount_amount=row[10],
                payment_method=row[11],
                items_count=row[12],
                status=row[13]
            ))
        
        conn.close()
        return sales
    
    def get_sales_analytics(self, 
                           store_id: str = None,
                           period_days: int = 30) -> Dict:
        """Obtener analíticas de ventas"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Query base
        store_filter = "AND store_id = ?" if store_id else ""
        params = [start_date, end_date]
        if store_id:
            params.append(store_id)
        
        # Totales del período
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_transactions,
                SUM(total_amount) as total_revenue,
                SUM(tax_amount) as total_tax,
                SUM(discount_amount) as total_discounts,
                SUM(items_count) as total_items,
                AVG(total_amount) as average_ticket
            FROM sales 
            WHERE sale_date BETWEEN ? AND ? {store_filter}
            AND status = 'completed'
        ''', params)
        
        totals = cursor.fetchone()
        
        # Ventas por día
        cursor.execute(f'''
            SELECT 
                DATE(sale_date) as sale_day,
                COUNT(*) as transactions,
                SUM(total_amount) as revenue,
                SUM(items_count) as items
            FROM sales 
            WHERE sale_date BETWEEN ? AND ? {store_filter}
            AND status = 'completed'
            GROUP BY DATE(sale_date)
            ORDER BY sale_day
        ''', params)
        
        daily_sales = cursor.fetchall()
        
        # Ventas por método de pago
        cursor.execute(f'''
            SELECT 
                payment_method,
                COUNT(*) as transactions,
                SUM(total_amount) as revenue
            FROM sales 
            WHERE sale_date BETWEEN ? AND ? {store_filter}
            AND status = 'completed'
            GROUP BY payment_method
            ORDER BY revenue DESC
        ''', params)
        
        payment_methods = cursor.fetchall()
        
        # Top productos
        cursor.execute(f'''
            SELECT 
                si.product_code,
                si.product_name,
                SUM(si.quantity) as total_quantity,
                SUM(si.line_total) as total_revenue,
                COUNT(DISTINCT si.sale_id) as transaction_count,
                AVG(si.unit_price) as average_price
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.sale_date BETWEEN ? AND ? {store_filter}
            AND s.status = 'completed'
            GROUP BY si.product_code, si.product_name
            ORDER BY total_quantity DESC
            LIMIT 20
        ''', params)
        
        top_products = cursor.fetchall()
        
        # Ventas por cajero
        cursor.execute(f'''
            SELECT 
                cashier_id,
                cashier_name,
                COUNT(*) as transactions,
                SUM(total_amount) as revenue,
                AVG(total_amount) as average_ticket
            FROM sales 
            WHERE sale_date BETWEEN ? AND ? {store_filter}
            AND status = 'completed'
            GROUP BY cashier_id, cashier_name
            ORDER BY revenue DESC
        ''', params)
        
        cashier_performance = cursor.fetchall()
        
        conn.close()
        
        return {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days': period_days
            },
            'totals': {
                'transactions': totals[0] or 0,
                'revenue': totals[1] or 0,
                'tax': totals[2] or 0,
                'discounts': totals[3] or 0,
                'items': totals[4] or 0,
                'average_ticket': totals[5] or 0
            },
            'daily_sales': [
                {
                    'date': row[0],
                    'transactions': row[1],
                    'revenue': row[2],
                    'items': row[3]
                } for row in daily_sales
            ],
            'payment_methods': [
                {
                    'method': row[0],
                    'transactions': row[1],
                    'revenue': row[2]
                } for row in payment_methods
            ],
            'top_products': [
                {
                    'code': row[0],
                    'name': row[1],
                    'quantity': row[2],
                    'revenue': row[3],
                    'transactions': row[4],
                    'average_price': row[5]
                } for row in top_products
            ],
            'cashier_performance': [
                {
                    'id': row[0],
                    'name': row[1],
                    'transactions': row[2],
                    'revenue': row[3],
                    'average_ticket': row[4]
                } for row in cashier_performance
            ]
        }
    
    def generate_sales_chart(self, analytics_data: Dict) -> str:
        """Generar gráfico de ventas (base64)"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Backend sin GUI
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # Gráfico 1: Ventas diarias
            daily_data = analytics_data['daily_sales']
            if daily_data:
                dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in daily_data]
                revenues = [d['revenue'] for d in daily_data]
                
                ax1.plot(dates, revenues, marker='o', linewidth=2, markersize=6)
                ax1.set_title('Ventas Diarias', fontsize=14, fontweight='bold')
                ax1.set_xlabel('Fecha')
                ax1.set_ylabel('Ingresos (₡)')
                ax1.grid(True, alpha=0.3)
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            
            # Gráfico 2: Métodos de pago
            payment_data = analytics_data['payment_methods']
            if payment_data:
                methods = [p['method'] for p in payment_data]
                revenues = [p['revenue'] for p in payment_data]
                
                colors = ['#3498db', '#e74c3c', '#f39c12', '#27ae60']
                ax2.pie(revenues, labels=methods, autopct='%1.1f%%', 
                       colors=colors[:len(methods)], startangle=90)
                ax2.set_title('Ventas por Método de Pago', fontsize=14, fontweight='bold')
            
            # Gráfico 3: Top productos
            product_data = analytics_data['top_products'][:10]
            if product_data:
                products = [p['name'][:20] + '...' if len(p['name']) > 20 else p['name'] for p in product_data]
                quantities = [p['quantity'] for p in product_data]
                
                bars = ax3.barh(products, quantities, color='#2ecc71')
                ax3.set_title('Top 10 Productos Más Vendidos', fontsize=14, fontweight='bold')
                ax3.set_xlabel('Cantidad Vendida')
                
                # Agregar valores en las barras
                for bar in bars:
                    width = bar.get_width()
                    ax3.text(width, bar.get_y() + bar.get_height()/2, 
                            f'{int(width)}', ha='left', va='center')
            
            # Gráfico 4: Performance de cajeros
            cashier_data = analytics_data['cashier_performance']
            if cashier_data:
                cashiers = [c['name'] for c in cashier_data]
                revenues = [c['revenue'] for c in cashier_data]
                
                bars = ax4.bar(cashiers, revenues, color='#9b59b6')
                ax4.set_title('Rendimiento por Cajero', fontsize=14, fontweight='bold')
                ax4.set_ylabel('Ingresos (₡)')
                ax4.tick_params(axis='x', rotation=45)
                
                # Agregar valores en las barras
                for bar in bars:
                    height = bar.get_height()
                    ax4.text(bar.get_x() + bar.get_width()/2., height,
                            f'₡{height:,.0f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            print(f"Error generando gráfico: {e}")
            return ""
    
    def export_to_excel(self, 
                       store_id: str = None,
                       start_date: datetime = None,
                       end_date: datetime = None,
                       filename: str = None) -> str:
        """Exportar datos a Excel"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"historial_ventas_{timestamp}.xlsx"
        
        # Obtener datos
        sales = self.get_sales_history(
            store_id=store_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        analytics = self.get_sales_analytics(store_id=store_id)
        
        # Crear DataFrame
        sales_data = []
        for sale in sales:
            sales_data.append({
                'ID Venta': sale.id,
                'Tienda': sale.store_name,
                'Cajero': sale.cashier_name,
                'Cliente': sale.customer_name or 'Cliente General',
                'Fecha': sale.sale_date.strftime('%d/%m/%Y %H:%M') if sale.sale_date else '',
                'Total': sale.total_amount,
                'IVA': sale.tax_amount,
                'Descuento': sale.discount_amount,
                'Método Pago': sale.payment_method,
                'Items': sale.items_count,
                'Estado': sale.status
            })
        
        df_sales = pd.DataFrame(sales_data)
        
        # Resumen
        summary_data = [
            ['Total Transacciones', analytics['totals']['transactions']],
            ['Ingresos Totales', f"₡{analytics['totals']['revenue']:,.2f}"],
            ['IVA Total', f"₡{analytics['totals']['tax']:,.2f}"],
            ['Descuentos Totales', f"₡{analytics['totals']['discounts']:,.2f}"],
            ['Items Vendidos', analytics['totals']['items']],
            ['Ticket Promedio', f"₡{analytics['totals']['average_ticket']:,.2f}"]
        ]
        
        df_summary = pd.DataFrame(summary_data, columns=['Concepto', 'Valor'])
        
        # Guardar en Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_sales.to_excel(writer, sheet_name='Historial Ventas', index=False)
            df_summary.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Top productos
            if analytics['top_products']:
                products_data = []
                for product in analytics['top_products']:
                    products_data.append({
                        'Código': product['code'],
                        'Producto': product['name'],
                        'Cantidad': product['quantity'],
                        'Ingresos': f"₡{product['revenue']:,.2f}",
                        'Transacciones': product['transactions'],
                        'Precio Promedio': f"₡{product['average_price']:,.2f}"
                    })
                
                df_products = pd.DataFrame(products_data)
                df_products.to_excel(writer, sheet_name='Top Productos', index=False)
        
        return filename
    
    def auto_update_on_startup(self):
        """Actualizar historial automáticamente al iniciar la aplicación"""
        try:
            # Simular carga de ventas recientes del POS
            # En producción esto leería de la base de datos principal del POS
            
            print("🔄 Actualizando historial de ventas...")
            
            # Ejemplo de venta para testing
            sample_sale = {
                'id': f"SALE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'store_id': 'store001',
                'store_name': 'Sucursal Principal',
                'cashier_id': 'cajero001',
                'cashier_name': 'María González',
                'customer_name': 'Cliente General',
                'sale_date': datetime.now(),
                'total_amount': 15750.00,
                'tax_amount': 1823.08,
                'discount_amount': 0.00,
                'payment_method': 'efectivo',
                'status': 'completed',
                'items': [
                    {
                        'product_code': '12345678',
                        'product_name': 'Arroz Premium 1kg',
                        'quantity': 2,
                        'unit_price': 2500.00,
                        'line_total': 5000.00
                    },
                    {
                        'product_code': '12345679',
                        'product_name': 'Aceite Vegetal 1L',
                        'quantity': 1,
                        'unit_price': 3200.00,
                        'line_total': 3200.00
                    }
                ]
            }
            
            # Registrar venta de ejemplo solo si no existe historial reciente
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM sales 
                WHERE sale_date >= date('now', '-1 day')
            ''')
            
            recent_sales = cursor.fetchone()[0]
            conn.close()
            
            if recent_sales == 0:
                self.record_sale(sample_sale)
                print("✅ Historial actualizado con datos de ejemplo")
            else:
                print(f"✅ Historial actualizado - {recent_sales} ventas recientes encontradas")
                
        except Exception as e:
            print(f"❌ Error actualizando historial: {e}")
    
    def get_real_time_stats(self) -> Dict:
        """Obtener estadísticas en tiempo real"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Ventas de hoy
        cursor.execute('''
            SELECT 
                COUNT(*) as today_transactions,
                COALESCE(SUM(total_amount), 0) as today_revenue,
                COALESCE(SUM(items_count), 0) as today_items
            FROM sales 
            WHERE DATE(sale_date) = ? AND status = 'completed'
        ''', (today,))
        
        today_stats = cursor.fetchone()
        
        # Comparación con ayer
        yesterday = (datetime.now() - timedelta(days=1)).date()
        cursor.execute('''
            SELECT 
                COUNT(*) as yesterday_transactions,
                COALESCE(SUM(total_amount), 0) as yesterday_revenue
            FROM sales 
            WHERE DATE(sale_date) = ? AND status = 'completed'
        ''', (yesterday,))
        
        yesterday_stats = cursor.fetchone()
        
        # Última venta
        cursor.execute('''
            SELECT sale_date, total_amount, cashier_name
            FROM sales 
            WHERE status = 'completed'
            ORDER BY sale_date DESC 
            LIMIT 1
        ''')
        
        last_sale = cursor.fetchone()
        
        conn.close()
        
        # Calcular variaciones
        revenue_change = 0
        if yesterday_stats[1] > 0:
            revenue_change = ((today_stats[1] - yesterday_stats[1]) / yesterday_stats[1]) * 100
        
        return {
            'today': {
                'transactions': today_stats[0],
                'revenue': today_stats[1],
                'items': today_stats[2]
            },
            'yesterday': {
                'transactions': yesterday_stats[0],
                'revenue': yesterday_stats[1]
            },
            'changes': {
                'revenue_percent': revenue_change
            },
            'last_sale': {
                'date': last_sale[0] if last_sale else None,
                'amount': last_sale[1] if last_sale else 0,
                'cashier': last_sale[2] if last_sale else ''
            }
        }
