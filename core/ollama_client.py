"""
Cliente Ollama optimizado para integración con el sistema POS
Maneja la comunicación con modelos locales de forma estable y eficiente
"""

import requests
import json
import subprocess
import time
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import threading
import queue
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OllamaResponse:
    """Respuesta estructurada de Ollama"""
    content: str
    model: str
    success: bool
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None

class OllamaClient:
    """Cliente robusto para Ollama con manejo de errores y recuperación automática"""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 ollama_path: str = r"C:\Users\bjorg\AppData\Local\Programs\Ollama\ollama.exe"):
        self.base_url = base_url
        self.ollama_path = ollama_path
        self.available_models = []
        self.current_model = None
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Cola para manejo asíncrono
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Estado del cliente
        self.is_healthy = False
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutos
        
        # Configuración de reintentos (más agresiva para estabilidad)
        self.max_retries = 2  # Reducir reintentos para respuestas más rápidas
        self.base_delay = 0.5  # Delay más corto
        
        # Inicializar
        self._initialize()
    
    def _initialize(self):
        """Inicializa el cliente y verifica la conexión"""
        try:
            logger.info("🤖 Inicializando cliente Ollama...")
            
            # Verificar que Ollama existe
            if not os.path.exists(self.ollama_path):
                logger.error(f"❌ Ollama no encontrado en: {self.ollama_path}")
                return
            
            # Verificar servicio Ollama
            if not self._is_ollama_running():
                logger.info("🚀 Iniciando servicio Ollama...")
                if self._start_ollama_service():
                    time.sleep(3)  # Esperar que inicie
                else:
                    logger.error("❌ No se pudo iniciar Ollama")
                    return
            
            # Cargar modelos disponibles
            self._load_available_models()
            
            # Seleccionar mejor modelo
            self._select_best_model()
            
            # Verificar salud
            self.is_healthy = self._health_check()
            
            if self.is_healthy:
                logger.info(f"✅ Cliente Ollama inicializado. Modelo activo: {self.current_model}")
            else:
                logger.warning("⚠️ Cliente Ollama inicializado pero con problemas de conectividad")
                
        except Exception as e:
            logger.error(f"❌ Error inicializando Ollama: {e}")
            self.is_healthy = False
    
    def _is_ollama_running(self) -> bool:
        """Verifica si el servicio Ollama está ejecutándose"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _start_ollama_service(self) -> bool:
        """Inicia el servicio Ollama en segundo plano"""
        try:
            # Intentar iniciar Ollama serve en segundo plano
            subprocess.Popen(
                [self.ollama_path, "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Esperar a que inicie (máximo 10 segundos)
            for _ in range(10):
                if self._is_ollama_running():
                    return True
                time.sleep(1)
            
            return False
        except Exception as e:
            logger.error(f"Error iniciando Ollama: {e}")
            return False
    
    def _load_available_models(self):
        """Carga la lista de modelos disponibles"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model["name"] for model in data.get("models", [])]
                logger.info(f"📋 Modelos disponibles: {', '.join(self.available_models)}")
            else:
                logger.warning("⚠️ No se pudieron cargar los modelos")
        except Exception as e:
            logger.error(f"Error cargando modelos: {e}")
            self.available_models = []
    
    def _select_best_model(self):
        """Selecciona el mejor modelo disponible para el POS"""
        if not self.available_models:
            logger.warning("⚠️ No hay modelos disponibles")
            return
        
        # Prioridad de modelos para el POS (ordenados por velocidad y eficiencia)
        preferred_models = [
            "llama3.2:3b",      # Más rápido y eficiente
            "llama3.2:1b",      # Super rápido
            "gemma2:2b",        # Pequeño y rápido
            "llama3.1:8b", 
            "gemma3:4b",        # Más lento pero más capaz
            "gemma2:9b",
            "gemma2:27b",
            "llama3:8b",
            "gemma:7b"
        ]
        
        # Buscar el mejor modelo disponible
        for preferred in preferred_models:
            for available in self.available_models:
                if preferred in available or available in preferred:
                    self.current_model = available
                    logger.info(f"🎯 Modelo seleccionado: {self.current_model}")
                    return
        
        # Si no encuentra uno preferido, usar el primero disponible
        if self.available_models:
            self.current_model = self.available_models[0]
            logger.info(f"🔄 Usando modelo fallback: {self.current_model}")
    
    def _health_check(self) -> bool:
        """Verifica la salud del cliente"""
        current_time = time.time()
        
        # Verificar si necesita health check
        if current_time - self.last_health_check < self.health_check_interval:
            return self.is_healthy
        
        try:
            # Test simple con el modelo actual
            if self.current_model:
                response = self._make_request(
                    "¿Funciona?", 
                    max_tokens=5, 
                    timeout=10
                )
                healthy = response.success
            else:
                healthy = self._is_ollama_running()
            
            self.last_health_check = current_time
            self.is_healthy = healthy
            
            if healthy:
                logger.debug("✅ Health check OK")
            else:
                logger.warning("⚠️ Health check fallido")
            
            return healthy
            
        except Exception as e:
            logger.error(f"❌ Error en health check: {e}")
            self.is_healthy = False
            return False
    
    def _make_request(self, prompt: str, max_tokens: int = 300, 
                     temperature: float = 0.7, timeout: int = 30) -> OllamaResponse:
        """Realiza una solicitud a Ollama con manejo de errores robusto"""
        
        if not self.current_model:
            return OllamaResponse(
                content="",
                model="none",
                success=False,
                error="No hay modelo disponible"
            )
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                # Preparar payload
                payload = {
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_ctx": 2048,  # Contexto más pequeño para velocidad
                        "num_batch": 512,  # Batch más pequeño
                        "num_gpu": 0,      # Forzar CPU para estabilidad
                        "low_vram": True   # Optimizar para recursos limitados
                    }
                }
                
                # Realizar solicitud
                response = self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    processing_time = time.time() - start_time
                    
                    return OllamaResponse(
                        content=data.get("response", "").strip(),
                        model=self.current_model,
                        success=True,
                        tokens_used=data.get("eval_count"),
                        processing_time=processing_time
                    )
                else:
                    logger.warning(f"⚠️ Respuesta HTTP {response.status_code} en intento {attempt + 1}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout en intento {attempt + 1}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Error de conexión en intento {attempt + 1}")
                # Intentar reiniciar Ollama
                if attempt == 0:
                    self._restart_ollama()
            except Exception as e:
                logger.error(f"❌ Error inesperado en intento {attempt + 1}: {e}")
            
            # Esperar antes del siguiente intento
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)  # Backoff exponencial
                time.sleep(delay)
        
        # Si todos los intentos fallaron
        processing_time = time.time() - start_time
        return OllamaResponse(
            content="",
            model=self.current_model or "unknown",
            success=False,
            error=f"Falló después de {self.max_retries} intentos",
            processing_time=processing_time
        )
    
    def _restart_ollama(self):
        """Intenta reiniciar el servicio Ollama"""
        try:
            logger.info("🔄 Intentando reiniciar Ollama...")
            
            # Matar procesos Ollama existentes
            subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], 
                         capture_output=True, text=True)
            
            time.sleep(2)
            
            # Reiniciar
            if self._start_ollama_service():
                logger.info("✅ Ollama reiniciado exitosamente")
                time.sleep(3)
                self._load_available_models()
            else:
                logger.error("❌ No se pudo reiniciar Ollama")
                
        except Exception as e:
            logger.error(f"❌ Error reiniciando Ollama: {e}")
    
    def ask(self, question: str, context: str = None, max_tokens: int = 300) -> OllamaResponse:
        """
        Realiza una pregunta al modelo de IA
        
        Args:
            question: Pregunta del usuario
            context: Contexto adicional (opcional)
            max_tokens: Máximo número de tokens en la respuesta
        """
        
        # Verificar salud del cliente
        if not self._health_check():
            return OllamaResponse(
                content="El servicio de IA no está disponible temporalmente.",
                model="none",
                success=False,
                error="Servicio no disponible"
            )
        
        # Construir prompt optimizado para POS
        system_prompt = """Eres un asistente experto en sistemas POS (Punto de Venta) para una caja registradora. 
Respondes de forma clara, concisa y práctica. Siempre das pasos específicos y útiles.
Tu objetivo es ayudar a usuarios del sistema de caja a resolver dudas rápidamente.
Mantén las respuestas breves pero completas."""
        
        if context:
            full_prompt = f"{system_prompt}\n\nContexto: {context}\n\nUsuario: {question}\nAsistente:"
        else:
            full_prompt = f"{system_prompt}\n\nUsuario: {question}\nAsistente:"
        
        return self._make_request(full_prompt, max_tokens)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información detallada del modelo actual"""
        if not self.current_model:
            return {"error": "No hay modelo activo"}
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/show",
                json={"name": self.current_model},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def list_models(self) -> List[str]:
        """Lista todos los modelos disponibles"""
        self._load_available_models()
        return self.available_models
    
    def switch_model(self, model_name: str) -> bool:
        """Cambia al modelo especificado"""
        if model_name in self.available_models:
            old_model = self.current_model
            self.current_model = model_name
            
            # Verificar que el modelo funciona
            if self._health_check():
                logger.info(f"🔄 Cambiado de {old_model} a {model_name}")
                return True
            else:
                # Revertir si no funciona
                self.current_model = old_model
                logger.error(f"❌ No se pudo cambiar a {model_name}")
                return False
        else:
            logger.error(f"❌ Modelo {model_name} no disponible")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del cliente"""
        return {
            "healthy": self.is_healthy,
            "current_model": self.current_model,
            "available_models": self.available_models,
            "total_models": len(self.available_models),
            "ollama_running": self._is_ollama_running(),
            "last_health_check": self.last_health_check,
            "base_url": self.base_url,
            "ollama_path": self.ollama_path
        }
    
    def benchmark_model(self, questions: List[str] = None) -> Dict[str, Any]:
        """Realiza un benchmark del modelo actual"""
        if not questions:
            questions = [
                "¿Cómo hacer una venta?",
                "¿Qué es un código de barras?",
                "Explica el proceso de facturación"
            ]
        
        results = []
        total_time = 0
        successful_requests = 0
        
        for question in questions:
            start_time = time.time()
            response = self.ask(question, max_tokens=100)
            end_time = time.time()
            
            request_time = end_time - start_time
            total_time += request_time
            
            if response.success:
                successful_requests += 1
            
            results.append({
                "question": question,
                "success": response.success,
                "response_time": request_time,
                "tokens": response.tokens_used,
                "content_length": len(response.content)
            })
        
        return {
            "model": self.current_model,
            "total_questions": len(questions),
            "successful_requests": successful_requests,
            "success_rate": successful_requests / len(questions),
            "average_response_time": total_time / len(questions),
            "total_time": total_time,
            "results": results
        }

# Instancia global del cliente
_ollama_client = None

def get_ollama_client() -> OllamaClient:
    """Obtiene la instancia global del cliente Ollama (Singleton)"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client

def test_ollama_integration():
    """Función de prueba para la integración"""
    print("🧪 Probando integración con Ollama...")
    
    client = get_ollama_client()
    status = client.get_status()
    
    print(f"📊 Estado: {'✅ Saludable' if status['healthy'] else '❌ Con problemas'}")
    print(f"🤖 Modelo actual: {status['current_model']}")
    print(f"📋 Modelos disponibles: {len(status['available_models'])}")
    
    if status['healthy']:
        # Prueba simple
        response = client.ask("¿Cómo hacer una venta en el POS?")
        print(f"\n💬 Pregunta de prueba:")
        print(f"✅ Éxito: {response.success}")
        print(f"📝 Respuesta: {response.content[:100]}...")
        print(f"⏱️ Tiempo: {response.processing_time:.2f}s")
    
    return status['healthy']

if __name__ == "__main__":
    test_ollama_integration()
