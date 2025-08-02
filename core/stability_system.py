"""
Sistema de Estabilidad para la Aplicación POS
Maneja errores, reintentos, logging y recuperación automática
"""

import logging
import logging.handlers
import traceback
import time
import os
import sys
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from dataclasses import dataclass, asdict
import psutil

# Configurar logging mejorado
def setup_logging():
    """Configura el sistema de logging avanzado"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Formato detallado
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s'
    )
    
    # Handler para archivo (rotativo)
    file_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/pos_stability.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para consola (solo errores importantes)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    console_handler.setLevel(logging.WARNING)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

@dataclass
class ErrorInfo:
    """Información detallada de un error"""
    timestamp: str
    error_type: str
    error_message: str
    function_name: str
    module_name: str
    traceback_info: str
    context: Dict[str, Any]
    severity: str  # 'low', 'medium', 'high', 'critical'
    user_impact: str  # 'none', 'minor', 'major', 'system_failure'

@dataclass 
class SystemMetrics:
    """Métricas del sistema para monitoreo"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    database_size_mb: float
    active_threads: int
    open_files: int
    response_time_ms: float

class StabilityManager:
    """Gestor de estabilidad del sistema POS"""
    
    def __init__(self, db_path: str = "data/stability.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.performance_metrics = []
        self.max_metrics_history = 1000
        
        # Configuración de reintentos
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_backoff": True
        }
        
        # Umbrales de alerta
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage": 90.0,
            "response_time_ms": 5000.0,
            "error_rate_per_hour": 10
        }
        
        self._initialize_database()
        self._start_monitoring_thread()
    
    def _initialize_database(self):
        """Inicializa la base de datos de estabilidad"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de errores
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS errors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        error_type TEXT NOT NULL,
                        error_message TEXT NOT NULL,
                        function_name TEXT,
                        module_name TEXT,
                        traceback_info TEXT,
                        context TEXT,
                        severity TEXT,
                        user_impact TEXT,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolution_notes TEXT
                    )
                """)
                
                # Tabla de métricas del sistema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_percent REAL,
                        memory_percent REAL,
                        disk_usage_percent REAL,
                        database_size_mb REAL,
                        active_threads INTEGER,
                        open_files INTEGER,
                        response_time_ms REAL
                    )
                """)
                
                # Tabla de configuración
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stability_config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                self.logger.info("✅ Base de datos de estabilidad inicializada")
                
        except Exception as e:
            self.logger.error(f"❌ Error inicializando BD estabilidad: {e}")
    
    def _start_monitoring_thread(self):
        """Inicia el hilo de monitoreo en segundo plano"""
        def monitor_loop():
            while True:
                try:
                    self._collect_system_metrics()
                    self._check_system_health()
                    time.sleep(60)  # Cada minuto
                except Exception as e:
                    self.logger.error(f"Error en monitoreo: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self.logger.info("🔍 Hilo de monitoreo iniciado")
    
    def _collect_system_metrics(self):
        """Recolecta métricas del sistema"""
        try:
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            # Información de la aplicación
            process = psutil.Process()
            active_threads = process.num_threads()
            open_files = len(process.open_files())
            
            # Tamaño de la base de datos
            db_size_mb = 0
            if os.path.exists("caja_registradora_pos_cr.db"):
                db_size_mb = os.path.getsize("caja_registradora_pos_cr.db") / (1024 * 1024)
            
            # Tiempo de respuesta (mock - se puede mejorar)
            start_time = time.time()
            # Simular operación de BD
            with sqlite3.connect(self.db_path, timeout=5) as conn:
                conn.execute("SELECT 1").fetchone()
            response_time_ms = (time.time() - start_time) * 1000
            
            # Crear métricas
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                database_size_mb=db_size_mb,
                active_threads=active_threads,
                open_files=open_files,
                response_time_ms=response_time_ms
            )
            
            # Guardar en BD
            self._save_metrics(metrics)
            
            # Mantener en memoria para análisis rápido
            self.performance_metrics.append(metrics)
            if len(self.performance_metrics) > self.max_metrics_history:
                self.performance_metrics.pop(0)
            
        except Exception as e:
            self.logger.error(f"Error recolectando métricas: {e}")
    
    def _save_metrics(self, metrics: SystemMetrics):
        """Guarda métricas en la base de datos"""
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_metrics 
                    (timestamp, cpu_percent, memory_percent, disk_usage_percent,
                     database_size_mb, active_threads, open_files, response_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
                    metrics.disk_usage_percent, metrics.database_size_mb,
                    metrics.active_threads, metrics.open_files, metrics.response_time_ms
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error guardando métricas: {e}")
    
    def _check_system_health(self):
        """Verifica la salud del sistema y genera alertas"""
        if not self.performance_metrics:
            return
        
        latest = self.performance_metrics[-1]
        alerts = []
        
        # Verificar umbrales
        if latest.cpu_percent > self.thresholds["cpu_percent"]:
            alerts.append(f"🔥 CPU alta: {latest.cpu_percent:.1f}%")
        
        if latest.memory_percent > self.thresholds["memory_percent"]:
            alerts.append(f"💾 Memoria alta: {latest.memory_percent:.1f}%")
        
        if latest.disk_usage_percent > self.thresholds["disk_usage"]:
            alerts.append(f"💿 Disco lleno: {latest.disk_usage_percent:.1f}%")
        
        if latest.response_time_ms > self.thresholds["response_time_ms"]:
            alerts.append(f"⏰ Respuesta lenta: {latest.response_time_ms:.0f}ms")
        
        # Verificar tendencias (últimos 5 minutos)
        if len(self.performance_metrics) >= 5:
            recent_metrics = self.performance_metrics[-5:]
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            
            if avg_cpu > self.thresholds["cpu_percent"] * 0.9:
                alerts.append(f"📈 Tendencia CPU alta: {avg_cpu:.1f}%")
            
            if avg_memory > self.thresholds["memory_percent"] * 0.9:
                alerts.append(f"📈 Tendencia memoria alta: {avg_memory:.1f}%")
        
        # Log alertas
        for alert in alerts:
            self.logger.warning(alert)
    
    def log_error(self, error: Exception, function_name: str = None, 
                  context: Dict[str, Any] = None, severity: str = "medium",
                  user_impact: str = "minor"):
        """Registra un error con información detallada"""
        try:
            # Obtener información del stack
            tb = traceback.extract_tb(error.__traceback__)
            if tb:
                last_frame = tb[-1]
                function_name = function_name or last_frame.name
                module_name = os.path.basename(last_frame.filename)
            else:
                module_name = "unknown"
            
            error_info = ErrorInfo(
                timestamp=datetime.now().isoformat(),
                error_type=type(error).__name__,
                error_message=str(error),
                function_name=function_name or "unknown",
                module_name=module_name,
                traceback_info=traceback.format_exc(),
                context=context or {},
                severity=severity,
                user_impact=user_impact
            )
            
            # Guardar en BD
            self._save_error(error_info)
            
            # Actualizar contador de errores
            error_key = f"{error_info.error_type}:{error_info.function_name}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Log según severidad
            log_msg = f"{error_info.error_type} en {error_info.function_name}: {error_info.error_message}"
            
            if severity == "critical":
                self.logger.critical(log_msg)
            elif severity == "high":
                self.logger.error(log_msg)
            elif severity == "medium":
                self.logger.warning(log_msg)
            else:
                self.logger.info(log_msg)
                
        except Exception as e:
            # Error logging el error - usar print como último recurso
            print(f"CRITICAL: Error en log_error: {e}")
    
    def _save_error(self, error_info: ErrorInfo):
        """Guarda información de error en la base de datos"""
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO errors 
                    (timestamp, error_type, error_message, function_name, module_name,
                     traceback_info, context, severity, user_impact)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    error_info.timestamp, error_info.error_type, error_info.error_message,
                    error_info.function_name, error_info.module_name, error_info.traceback_info,
                    json.dumps(error_info.context), error_info.severity, error_info.user_impact
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error guardando info de error: {e}")

# Decorador para manejo automático de errores
def handle_errors(severity: str = "medium", user_impact: str = "minor", 
                 retry: bool = False, fallback_value: Any = None):
    """
    Decorador para manejo automático de errores con logging y reintentos
    
    Args:
        severity: Nivel de severidad del error
        user_impact: Impacto en el usuario
        retry: Si debe reintentar en caso de error
        fallback_value: Valor a retornar si falla
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            stability_manager = get_stability_manager()
            
            for attempt in range(stability_manager.retry_config["max_retries"] if retry else 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    # Log del error
                    context = {
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                        "attempt": attempt + 1
                    }
                    
                    stability_manager.log_error(
                        error=e,
                        function_name=func.__name__,
                        context=context,
                        severity=severity,
                        user_impact=user_impact
                    )
                    
                    # Si no es el último intento y se debe reintentar
                    if retry and attempt < stability_manager.retry_config["max_retries"] - 1:
                        delay = stability_manager.retry_config["base_delay"] * (2 ** attempt)
                        delay = min(delay, stability_manager.retry_config["max_delay"])
                        time.sleep(delay)
                        continue
                    
                    # Si llegamos aquí, falló definitivamente
                    if fallback_value is not None:
                        return fallback_value
                    else:
                        raise e
            
        return wrapper
    return decorator

# Decorador para medición de rendimiento
def measure_performance(track_args: bool = False):
    """Decorador para medir rendimiento de funciones"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                success = True
                error_info = None
            except Exception as e:
                result = None
                success = False
                error_info = str(e)
                raise
            finally:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Log rendimiento
                context = {
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "success": success,
                    "error": error_info
                }
                
                if track_args:
                    context.update({
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    })
                
                logger = logging.getLogger(func.__module__)
                if duration_ms > 1000:  # Más de 1 segundo
                    logger.warning(f"⏰ {func.__name__} tardó {duration_ms:.0f}ms")
                else:
                    logger.debug(f"⚡ {func.__name__}: {duration_ms:.1f}ms")
            
            return result
        return wrapper
    return decorator

class HealthChecker:
    """Verificador de salud del sistema"""
    
    def __init__(self, stability_manager: StabilityManager):
        self.stability_manager = stability_manager
        self.logger = logging.getLogger(__name__)
    
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Realiza un chequeo completo de salud del sistema"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "checks": {}
        }
        
        # Lista de verificaciones
        checks = [
            ("database", self._check_database),
            ("filesystem", self._check_filesystem),
            ("memory", self._check_memory),
            ("cpu", self._check_cpu),
            ("disk_space", self._check_disk_space),
            ("ai_engines", self._check_ai_engines),
            ("network", self._check_network)
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_func in checks:
            try:
                check_result = check_func()
                results["checks"][check_name] = check_result
                if check_result.get("status") == "ok":
                    passed_checks += 1
            except Exception as e:
                results["checks"][check_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Determinar estado general
        health_percentage = (passed_checks / total_checks) * 100
        
        if health_percentage >= 90:
            results["overall_status"] = "excellent"
        elif health_percentage >= 75:
            results["overall_status"] = "good"
        elif health_percentage >= 50:
            results["overall_status"] = "fair"
        else:
            results["overall_status"] = "poor"
        
        results["health_percentage"] = health_percentage
        results["passed_checks"] = passed_checks
        results["total_checks"] = total_checks
        
        return results
    
    def _check_database(self) -> Dict[str, Any]:
        """Verifica el estado de la base de datos"""
        try:
            # Verificar conexión
            with sqlite3.connect("caja_registradora_pos_cr.db", timeout=5) as conn:
                cursor = conn.cursor()
                
                # Test básico
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
                # Verificar integridad
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                
                return {
                    "status": "ok" if integrity == "ok" else "warning",
                    "table_count": table_count,
                    "integrity": integrity,
                    "file_size_mb": os.path.getsize("caja_registradora_pos_cr.db") / (1024 * 1024)
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_filesystem(self) -> Dict[str, Any]:
        """Verifica el sistema de archivos"""
        try:
            required_dirs = ["data", "logs", "temp", "backups"]
            missing_dirs = []
            
            for dir_name in required_dirs:
                if not os.path.exists(dir_name):
                    missing_dirs.append(dir_name)
            
            # Verificar permisos de escritura
            test_file = "temp/write_test.tmp"
            can_write = True
            try:
                os.makedirs(os.path.dirname(test_file), exist_ok=True)
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except:
                can_write = False
            
            return {
                "status": "ok" if not missing_dirs and can_write else "warning",
                "missing_directories": missing_dirs,
                "can_write": can_write
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_memory(self) -> Dict[str, Any]:
        """Verifica el uso de memoria"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            
            process_memory_mb = process.memory_info().rss / (1024 * 1024)
            
            return {
                "status": "ok" if memory.percent < 85 else "warning",
                "system_memory_percent": memory.percent,
                "process_memory_mb": process_memory_mb,
                "available_gb": memory.available / (1024 * 1024 * 1024)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_cpu(self) -> Dict[str, Any]:
        """Verifica el uso de CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            return {
                "status": "ok" if cpu_percent < 80 else "warning",
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Verifica el espacio en disco"""
        try:
            disk = psutil.disk_usage('.')
            usage_percent = (disk.used / disk.total) * 100
            
            return {
                "status": "ok" if usage_percent < 90 else "warning",
                "usage_percent": usage_percent,
                "free_gb": disk.free / (1024 * 1024 * 1024),
                "total_gb": disk.total / (1024 * 1024 * 1024)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_ai_engines(self) -> Dict[str, Any]:
        """Verifica el estado de los engines de IA"""
        try:
            from core.ai_assistant import POSAIAssistant
            from core.database import DatabaseManager
            
            db_manager = DatabaseManager()
            ai = POSAIAssistant(db_manager)
            status = ai.get_engine_status()
            
            return {
                "status": "ok" if status["active_engines"] else "warning",
                "active_engines": status["active_engines"],
                "engines_count": len(status["active_engines"]),
                "details": status
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_network(self) -> Dict[str, Any]:
        """Verifica la conectividad de red"""
        try:
            import socket
            
            # Test conexión local (Ollama)
            ollama_available = False
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex(('localhost', 11434))
                ollama_available = result == 0
                sock.close()
            except:
                pass
            
            return {
                "status": "ok",
                "ollama_service": ollama_available
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Instancia global del gestor de estabilidad
_stability_manager = None

def get_stability_manager() -> StabilityManager:
    """Obtiene la instancia global del gestor de estabilidad"""
    global _stability_manager
    if _stability_manager is None:
        _stability_manager = StabilityManager()
    return _stability_manager

def initialize_stability_system():
    """Inicializa el sistema completo de estabilidad"""
    # Configurar logging
    setup_logging()
    
    # Inicializar gestor de estabilidad
    stability_manager = get_stability_manager()
    
    # Configurar manejo global de excepciones
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        stability_manager.log_error(
            error=exc_value,
            function_name="global_exception_handler",
            severity="critical",
            user_impact="system_failure"
        )
        
        # También llamar al handler original
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = handle_exception
    
    logging.getLogger(__name__).info("🛡️ Sistema de estabilidad inicializado")
    
    return stability_manager

if __name__ == "__main__":
    # Test del sistema de estabilidad
    initialize_stability_system()
    
    stability_manager = get_stability_manager() 
    health_checker = HealthChecker(stability_manager)
    
    print("🧪 Probando sistema de estabilidad...")
    
    # Test de health check
    health_results = health_checker.comprehensive_health_check()
    print(f"📊 Estado general: {health_results['overall_status']}")
    print(f"✅ Verificaciones pasadas: {health_results['passed_checks']}/{health_results['total_checks']}")
    
    # Test de manejo de errores
    @handle_errors(severity="low", retry=True, fallback_value="Error handled")
    def test_function():
        raise ValueError("Error de prueba")
    
    result = test_function()
    print(f"🔧 Resultado con manejo de errores: {result}")
    
    print("✅ Sistema de estabilidad funcionando correctamente")
