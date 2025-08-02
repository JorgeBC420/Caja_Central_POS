"""
Asistente de IA Híbrido para el Sistema POS
Combina múltiples engines: Local (ChatterBot) + Cloud (Llama) + Reglas
Ayuda con funciones básicas y responde preguntas sobre el sistema
"""

import json
import re
import random
import requests
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from core.database import DatabaseManager

# Intentar importar dependencias opcionales
try:
    from chatterbot import ChatBot
    from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer
    CHATTERBOT_AVAILABLE = True
except ImportError:
    CHATTERBOT_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from core.ollama_client import get_ollama_client, OllamaClient
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

class POSAIAssistant:
    """Asistente de IA híbrido para el sistema POS"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager
        self.knowledge_base = self._load_knowledge_base()
        self.conversation_history = []
        self.active_engines = []
        
        # Configuración de backends
        self.config = {
            "use_chatterbot": CHATTERBOT_AVAILABLE,
            "use_transformers": TRANSFORMERS_AVAILABLE,
            "use_ollama": OLLAMA_AVAILABLE,
            "use_llama_api": False,  # Se activa si hay API key
            "llama_api_url": "http://localhost:5001/completion",
            "fireworks_api_key": None,
            "fallback_to_rules": True
        }
        
        # Inicializar engines disponibles
        self._initialize_engines()
        
    def _initialize_engines(self):
        """Inicializa los diferentes engines de IA disponibles"""
        
        # 1. ChatterBot (Local, entrenado)
        if self.config["use_chatterbot"]:
            try:
                self.chatbot = ChatBot(
                    'POSAssistant',
                    storage_adapter='chatterbot.storage.SQLStorageAdapter',
                    database_uri='sqlite:///pos_chatbot.db',
                    logic_adapters=[
                        'chatterbot.logic.BestMatch',
                        'chatterbot.logic.MathematicalEvaluation',
                    ]
                )
                self._train_chatterbot()
                self.active_engines.append("chatterbot")
            except Exception as e:
                print(f"ChatterBot no disponible: {e}")
                self.config["use_chatterbot"] = False
        
        # 2. Transformers (Local, QA)
        if self.config["use_transformers"]:
            try:
                self.qa_pipeline = pipeline(
                    "question-answering",
                    model="distilbert-base-cased-distilled-squad",
                    return_all_scores=True
                )
                self.active_engines.append("transformers")
            except Exception as e:
                print(f"Transformers no disponible: {e}")
                self.config["use_transformers"] = False
        
        # 3. Ollama (Local, Avanzado)
        if self.config["use_ollama"]:
            try:
                self.ollama_client = get_ollama_client()
                if self.ollama_client.is_healthy:
                    self.active_engines.append("ollama")
                    print(f"✅ Ollama conectado: {self.ollama_client.current_model}")
                else:
                    print("⚠️ Ollama disponible pero no saludable")
                    self.config["use_ollama"] = False
            except Exception as e:
                print(f"Ollama no disponible: {e}")
                self.config["use_ollama"] = False
        
        # 4. Llama API (Cloud/Local) - Deprecado en favor de Ollama
        if self._test_llama_connection():
            self.active_engines.append("llama_api")
            self.config["use_llama_api"] = True
        
        print(f"🤖 Engines AI activos: {', '.join(self.active_engines)}")
    
    def _train_chatterbot(self):
        """Entrena ChatterBot con datos específicos del POS"""
        if not hasattr(self, 'chatbot'):
            return
            
        trainer = ListTrainer(self.chatbot)
        
        # Datos de entrenamiento específicos del POS
        training_data = [
            "¿Cómo crear una venta?",
            "Ve a 'Ventas' > 'Nueva Venta', busca productos con F2 y presiona F3 para cobrar",
            
            "¿Cómo buscar un producto?",
            "Presiona F2 o ve a 'Inventario' > 'Buscar'. Puedes usar código, nombre o código de barras",
            
            "¿Cómo hacer una devolución?",
            "Ve a 'Ventas' > 'Devoluciones', busca la venta original y selecciona productos a devolver",
            
            "¿Cómo ver reportes?",
            "Presiona F5 o ve a 'Reportes'. Ahí encontrarás ventas diarias, inventario y más",
            
            "¿Cómo cerrar la caja?",
            "Ve a 'Caja' > 'Cierre de Caja', revisa los totales y confirma el cierre",
            
            "¿Cómo agregar un producto?",
            "Ve a 'Inventario' > 'Productos' > 'Agregar' (Ctrl+N) y completa la información",
            
            "¿Cómo imprimir un ticket?",
            "Al completar una venta se imprime automáticamente. Para duplicados: 'Ventas' > 'Historial' > 'Reimprimir'",
            
            "¿Qué atajos de teclado hay?",
            "F1: Nueva venta, F2: Buscar producto, F3: Cobrar, F4: Calculadora, F5: Reportes, F9: Ayuda",
            
            "Error: producto no encontrado",
            "Verifica el código o nombre. Usa '*' para búsquedas parciales. Revisa que el producto esté en inventario",
            
            "Error de impresión",
            "Revisa que la impresora esté conectada y tenga papel. Ve a 'Configuración' > 'Impresoras'",
        ]
        
        # Entrenar con los datos
        trainer.train(training_data)
        
        # Entrenar con corpus en español si está disponible
        try:
            corpus_trainer = ChatterBotCorpusTrainer(self.chatbot)
            corpus_trainer.train("chatterbot.corpus.spanish")
        except:
            pass  # Corpus no disponible
    
    def _test_llama_connection(self) -> bool:
        """Prueba conexión con Llama API"""
        try:
            response = requests.post(
                self.config["llama_api_url"],
                json={"prompt": "Test", "max_tokens": 1},
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
        
    def _load_knowledge_base(self) -> Dict:
        """Carga la base de conocimientos del sistema POS"""
        return {
            "funciones_basicas": {
                "realizar_venta": {
                    "descripcion": "Para realizar una venta: 1) Busca el producto, 2) Agrega cantidad, 3) Selecciona método de pago, 4) Procesa la venta",
                    "pasos": [
                        "Ir a la pestaña 'Ventas'",
                        "Buscar producto por código, nombre o código de barras",
                        "Especificar cantidad",
                        "Agregar al carrito",
                        "Seleccionar método de pago (efectivo, tarjeta, mixto)",
                        "Procesar venta e imprimir ticket"
                    ],
                    "atajos": ["F1: Nueva venta", "F2: Buscar producto", "F3: Cobrar"]
                },
                "buscar_producto": {
                    "descripcion": "Busca productos por código, nombre, código de barras o categoría",
                    "metodos": ["Por código", "Por nombre", "Por código de barras", "Por categoría"],
                    "tips": ["Usa * para búsquedas parciales", "Puedes escanear códigos de barras"]
                },
                "gestionar_inventario": {
                    "descripcion": "Controla el stock, precios y datos de productos",
                    "acciones": ["Ver stock", "Actualizar precios", "Agregar productos", "Ver movimientos"]
                },
                "reportes": {
                    "descripcion": "Genera reportes de ventas, inventario y finanzas",
                    "tipos": ["Ventas diarias", "Productos más vendidos", "Estado de caja", "Inventario bajo"]
                },
                "clientes": {
                    "descripcion": "Gestiona información de clientes y facturación",
                    "funciones": ["Registrar cliente", "Buscar cliente", "Historial de compras"]
                }
            },
            "preguntas_frecuentes": {
                "¿cómo cobro una venta?": "Ve a Ventas > Agregar productos > Seleccionar método de pago > Procesar venta",
                "¿cómo busco un producto?": "Usa F2 o ve a Inventario > Buscar. Puedes buscar por código, nombre o escanear código de barras",
                "¿cómo hago una devolución?": "Ve a Ventas > Devoluciones > Buscar venta original > Seleccionar productos a devolver",
                "¿cómo veo las ventas del día?": "Ve a Reportes > Ventas diarias o presiona F5",
                "¿cómo agrego un producto nuevo?": "Ve a Inventario > Productos > Agregar nuevo > Completa los datos",
                "¿cómo hago un descuento?": "En la venta, selecciona el producto > Aplicar descuento > Especifica porcentaje o monto",
                "¿cómo imprimo un duplicado?": "Ve a Ventas > Historial > Buscar venta > Reimprimir ticket",
                "¿cómo cierro la caja?": "Ve a Caja > Cierre de caja > Revisar totales > Confirmar cierre"
            },
            "atajos_teclado": {
                "F1": "Nueva venta",
                "F2": "Buscar producto", 
                "F3": "Procesar pago",
                "F4": "Calculadora",
                "F5": "Reportes rápidos",
                "F6": "Gestión de clientes",
                "F7": "Inventario",
                "F8": "Configuración",
                "F9": "Ayuda",
                "F10": "Cerrar caja",
                "Ctrl+N": "Nuevo producto",
                "Ctrl+S": "Guardar",
                "Ctrl+P": "Imprimir",
                "Esc": "Cancelar operación"
            },
            "errores_comunes": {
                "producto no encontrado": "Verifica el código o nombre. Usa búsqueda parcial con *",
                "stock insuficiente": "El producto no tiene suficiente stock. Verifica inventario",
                "error de impresión": "Revisa que la impresora esté conectada y con papel",
                "error de pago": "Verifica el método de pago y conexión de red para tarjetas",
                "base de datos bloqueada": "Cierra otras instancias del programa"
            }
        }
    
    def ask(self, question: str, context: str = None, use_engine: str = "auto") -> Dict[str, Any]:
        """
        Procesa una pregunta usando múltiples engines de IA
        
        Args:
            question: Pregunta del usuario
            context: Contexto adicional
            use_engine: Engine específico a usar ("auto", "chatterbot", "transformers", "llama", "rules")
        """
        question = question.strip()
        
        # Agregar a historial
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "context": context,
            "type": "user"
        })
        
        # Determinar mejor engine
        if use_engine == "auto":
            use_engine = self._select_best_engine(question)
        
        # Procesar con el engine seleccionado
        response = self._process_with_engine(question, context, use_engine)
        
        # Agregar respuesta al historial
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "response": response,
            "engine_used": use_engine,
            "type": "assistant"
        })
        
        return response
    
    def _select_best_engine(self, question: str) -> str:
        """Selecciona el mejor engine basado en la pregunta"""
        question_lower = question.lower()
        
        # Preguntas complejas o conversacionales -> Ollama (mejor modelo)
        if any(word in question_lower for word in ["explicar", "detallar", "paso a paso", "tutorial", "por favor", "ayúdame"]):
            if "ollama" in self.active_engines:
                return "ollama"
        
        # Preguntas técnicas avanzadas -> Ollama
        if any(word in question_lower for word in ["configurar", "instalar", "problema", "error", "solucionar"]):
            if "ollama" in self.active_engines:
                return "ollama"
        
        # Preguntas específicas del POS -> ChatterBot (entrenado) o Ollama
        if any(word in question_lower for word in ["cómo", "como", "venta", "producto", "caja", "ticket", "factura"]):
            if "ollama" in self.active_engines:
                return "ollama"
            elif "chatterbot" in self.active_engines:
                return "chatterbot"
        
        # Preguntas con contexto largo -> Ollama o Transformers
        if len(question.split()) > 10:
            if "ollama" in self.active_engines:
                return "ollama"
            elif "transformers" in self.active_engines:
                return "transformers"
        
        # Prioridad: Ollama > ChatterBot > Transformers > Llama API > Rules
        priority_engines = ["ollama", "chatterbot", "transformers", "llama_api", "rules"]
        for engine in priority_engines:
            if engine in self.active_engines:
                return engine
        
        return "rules"
    
    def _process_with_engine(self, question: str, context: str, engine: str) -> Dict[str, Any]:
        """Procesa la pregunta con el engine especificado"""
        
        try:
            if engine == "chatterbot" and hasattr(self, 'chatbot'):
                return self._ask_chatterbot(question)
            
            elif engine == "transformers" and hasattr(self, 'qa_pipeline'):
                return self._ask_transformers(question, context)
            
            elif engine == "ollama" and hasattr(self, 'ollama_client'):
                return self._ask_ollama(question, context)
            
            elif engine == "llama_api" and self.config["use_llama_api"]:
                return self._ask_llama_api(question, context)
            
            else:
                return self._ask_rules_based(question)
                
        except Exception as e:
            print(f"Error en engine {engine}: {e}")
            # Fallback a reglas
            return self._ask_rules_based(question)
    
    def _ask_chatterbot(self, question: str) -> Dict[str, Any]:
        """Pregunta usando ChatterBot"""
        response = self.chatbot.get_response(question)
        confidence = response.confidence if hasattr(response, 'confidence') else 0.8
        
        return {
            "type": "chatterbot",
            "title": "Asistente POS",
            "answer": str(response),
            "confidence": confidence,
            "engine": "chatterbot",
            "suggestions": self._get_related_questions(question)
        }
    
    def _ask_transformers(self, question: str, context: str = None) -> Dict[str, Any]:
        """Pregunta usando Transformers QA"""
        if not context:
            # Crear contexto desde knowledge base
            context = self._build_context_from_kb(question)
        
        if not context:
            return self._ask_rules_based(question)
        
        result = self.qa_pipeline(question=question, context=context)
        
        return {
            "type": "transformers",
            "title": "Análisis IA",
            "answer": result['answer'],
            "confidence": result['score'],
            "engine": "transformers",
            "context_used": context[:100] + "..." if len(context) > 100 else context
        }
    
    def _ask_ollama(self, question: str, context: str = None) -> Dict[str, Any]:
        """Pregunta usando Ollama (modelo local avanzado)"""
        try:
            # Verificar que Ollama esté saludable
            if not self.ollama_client.is_healthy:
                # Intentar reconectar
                self.ollama_client._health_check()
                if not self.ollama_client.is_healthy:
                    return self._ask_rules_based(question)
            
            # Realizar pregunta con contexto POS
            response = self.ollama_client.ask(question, context, max_tokens=300)
            
            if response.success:
                return {
                    "type": "ollama",
                    "title": f"Asistente IA ({response.model})",
                    "answer": response.content,
                    "confidence": 0.95 if response.processing_time < 5 else 0.85,
                    "engine": "ollama",
                    "model_used": response.model,
                    "processing_time": response.processing_time,
                    "tokens_used": response.tokens_used,
                    "suggestions": self._get_related_questions(question)
                }
            else:
                print(f"⚠️ Error Ollama: {response.error}")
                return self._ask_rules_based(question)
                
        except Exception as e:
            print(f"❌ Error crítico Ollama: {e}")
            return self._ask_rules_based(question)
    
    def _ask_llama_api(self, question: str, context: str = None) -> Dict[str, Any]:
        """Pregunta usando Llama API"""
        
        # Crear prompt específico para POS
        system_prompt = """Eres un asistente experto en sistemas POS (Punto de Venta). 
Respondes de forma clara, concisa y práctica. Siempre das pasos específicos.
Tu objetivo es ayudar a usuarios del sistema de caja a resolver dudas rápidamente."""
        
        if context:
            prompt = f"{system_prompt}\n\nContexto: {context}\n\nUsuario: {question}\nAsistente:"
        else:
            prompt = f"{system_prompt}\n\nUsuario: {question}\nAsistente:"
        
        try:
            response = requests.post(
                self.config["llama_api_url"],
                json={
                    "prompt": prompt,
                    "max_tokens": 300,
                    "temperature": 0.7,
                    "stop": ["Usuario:", "\n\n"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("content", "").strip()
                
                return {
                    "type": "llama_api",
                    "title": "Asistente IA Avanzado",
                    "answer": answer,
                    "confidence": 0.9,
                    "engine": "llama_api",
                    "model_used": result.get("model", "llama")
                }
        
        except Exception as e:
            print(f"Error Llama API: {e}")
        
        # Fallback
        return self._ask_rules_based(question)
    
    def _ask_rules_based(self, question: str) -> Dict[str, Any]:
        """Pregunta usando sistema de reglas (fallback)"""
        return self._process_question(question)  # Método original
    
    def _build_context_from_kb(self, question: str) -> str:
        """Construye contexto relevante desde la knowledge base"""
        question_lower = question.lower()
        relevant_context = []
        
        # Buscar en funciones básicas
        for func_name, func_data in self.knowledge_base["funciones_basicas"].items():
            if any(word in question_lower for word in func_name.split("_")):
                relevant_context.append(f"{func_name}: {func_data['descripcion']}")
        
        # Buscar en FAQ
        for faq_q, faq_a in self.knowledge_base["preguntas_frecuentes"].items():
            if self._similarity_match(question, faq_q, threshold=0.4):
                relevant_context.append(f"FAQ: {faq_q} - {faq_a}")
        
        return " ".join(relevant_context[:3])  # Top 3 más relevantes
    
    def _get_related_questions(self, question: str) -> List[str]:
        """Obtiene preguntas relacionadas"""
        related = []
        question_words = set(question.lower().split())
        
        for faq_q in self.knowledge_base["preguntas_frecuentes"].keys():
            faq_words = set(faq_q.lower().split())
            if len(question_words.intersection(faq_words)) >= 1:
                related.append(faq_q)
        
        return related[:3]
    
    def _process_question(self, question: str) -> Dict[str, Any]:
        """Procesa la pregunta y genera una respuesta"""
        
        # Detectar tipo de pregunta
        if any(word in question for word in ["cómo", "como", "how"]):
            return self._handle_how_to_question(question)
        elif any(word in question for word in ["qué", "que", "what"]):
            return self._handle_what_question(question)
        elif any(word in question for word in ["dónde", "donde", "where"]):
            return self._handle_where_question(question)
        elif any(word in question for word in ["error", "problema", "no funciona"]):
            return self._handle_error_question(question)
        elif any(word in question for word in ["atajo", "tecla", "shortcut"]):
            return self._handle_shortcut_question(question)
        else:
            return self._handle_general_question(question)
    
    def _handle_how_to_question(self, question: str) -> Dict[str, Any]:
        """Maneja preguntas de 'cómo hacer' algo"""
        
        # Buscar en preguntas frecuentes
        for faq_q, faq_a in self.knowledge_base["preguntas_frecuentes"].items():
            if self._similarity_match(question, faq_q):
                return {
                    "type": "how_to",
                    "title": "Cómo hacer esta acción",
                    "answer": faq_a,
                    "confidence": 0.9
                }
        
        # Buscar en funciones básicas
        if "venta" in question or "cobrar" in question or "vender" in question:
            func_data = self.knowledge_base["funciones_basicas"]["realizar_venta"]
            return {
                "type": "how_to",
                "title": "Cómo realizar una venta",
                "answer": func_data["descripcion"],
                "steps": func_data["pasos"],
                "shortcuts": func_data["atajos"],
                "confidence": 0.95
            }
        
        elif "producto" in question and ("buscar" in question or "encontrar" in question):
            func_data = self.knowledge_base["funciones_basicas"]["buscar_producto"]
            return {
                "type": "how_to",
                "title": "Cómo buscar productos",
                "answer": func_data["descripcion"],
                "methods": func_data["metodos"],
                "tips": func_data["tips"],
                "confidence": 0.9
            }
        
        elif "inventario" in question:
            func_data = self.knowledge_base["funciones_basicas"]["gestionar_inventario"]
            return {
                "type": "how_to",
                "title": "Gestión de inventario",
                "answer": func_data["descripcion"],
                "actions": func_data["acciones"],
                "confidence": 0.85
            }
        
        return {
            "type": "how_to",
            "title": "Instrucciones generales",
            "answer": "Para ayudarte mejor, ¿podrías ser más específico? Por ejemplo: '¿cómo cobro una venta?' o '¿cómo busco un producto?'",
            "suggestions": list(self.knowledge_base["preguntas_frecuentes"].keys())[:5],
            "confidence": 0.5
        }
    
    def _handle_error_question(self, question: str) -> Dict[str, Any]:
        """Maneja preguntas sobre errores"""
        
        for error, solution in self.knowledge_base["errores_comunes"].items():
            if any(word in question for word in error.split()):
                return {
                    "type": "error_help",
                    "title": f"Solución para: {error}",
                    "answer": solution,
                    "confidence": 0.8
                }
        
        return {
            "type": "error_help",
            "title": "Ayuda con errores",
            "answer": "Describe el error específico que estás experimentando para poder ayudarte mejor.",
            "common_errors": list(self.knowledge_base["errores_comunes"].keys()),
            "confidence": 0.6
        }
    
    def _handle_shortcut_question(self, question: str) -> Dict[str, Any]:
        """Maneja preguntas sobre atajos de teclado"""
        
        return {
            "type": "shortcuts",
            "title": "Atajos de teclado disponibles",
            "answer": "Aquí tienes los atajos más útiles:",
            "shortcuts": self.knowledge_base["atajos_teclado"],
            "confidence": 0.9
        }
    
    def _handle_general_question(self, question: str) -> Dict[str, Any]:
        """Maneja preguntas generales"""
        
        # Buscar palabras clave
        if "venta" in question:
            return self._get_function_help("realizar_venta")
        elif "producto" in question or "inventario" in question:
            return self._get_function_help("gestionar_inventario")
        elif "cliente" in question:
            return self._get_function_help("clientes")
        elif "reporte" in question:
            return self._get_function_help("reportes")
        
        return {
            "type": "general",
            "title": "Asistente POS",
            "answer": "¡Hola! Soy tu asistente del sistema POS. Puedo ayudarte con:",
            "capabilities": [
                "Explicar cómo usar las funciones del sistema",
                "Resolver errores comunes",
                "Mostrar atajos de teclado",
                "Guiar paso a paso en procesos"
            ],
            "examples": [
                "¿Cómo cobro una venta?",
                "¿Cómo busco un producto?",
                "¿Qué atajos de teclado hay?",
                "Error: producto no encontrado"
            ],
            "confidence": 0.7
        }
    
    def _get_function_help(self, function_name: str) -> Dict[str, Any]:
        """Obtiene ayuda para una función específica"""
        
        if function_name in self.knowledge_base["funciones_basicas"]:
            func_data = self.knowledge_base["funciones_basicas"][function_name]
            return {
                "type": "function_help",
                "title": f"Ayuda: {function_name.replace('_', ' ').title()}",
                "answer": func_data["descripcion"],
                "details": func_data,
                "confidence": 0.9
            }
        
        return {
            "type": "function_help",
            "title": "Función no encontrada",
            "answer": f"No encontré información específica sobre '{function_name}'",
            "confidence": 0.3
        }
    
    def _similarity_match(self, text1: str, text2: str, threshold: float = 0.6) -> bool:
        """Calcula similitud básica entre dos textos"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def get_contextual_help(self, current_window: str) -> Dict[str, Any]:
        """Proporciona ayuda contextual basada en la ventana actual"""
        
        context_help = {
            "ventas": {
                "title": "Ayuda: Módulo de Ventas",
                "description": "Estás en el módulo de ventas. Aquí puedes:",
                "actions": [
                    "Buscar productos (F2)",
                    "Agregar al carrito",
                    "Aplicar descuentos",
                    "Procesar pago (F3)",
                    "Imprimir ticket"
                ],
                "tips": [
                    "Usa el escáner para códigos de barras",
                    "Presiona Enter para agregar cantidad rápidamente",
                    "F1 para nueva venta"
                ]
            },
            "inventario": {
                "title": "Ayuda: Gestión de Inventario",
                "description": "Gestiona tus productos y stock:",
                "actions": [
                    "Ver productos existentes",
                    "Agregar nuevos productos (Ctrl+N)",
                    "Actualizar precios",
                    "Controlar stock",
                    "Ver movimientos"
                ]
            },
            "reportes": {
                "title": "Ayuda: Reportes",
                "description": "Genera reportes y estadísticas:",
                "actions": [
                    "Ventas del día",
                    "Productos más vendidos",
                    "Estado de caja",
                    "Inventario con stock bajo"
                ]
            }
        }
        
        return context_help.get(current_window.lower(), {
            "title": "Ayuda General",
            "description": "Sistema POS - Presiona F9 para ayuda completa"
        })
    
    def get_quick_tips(self) -> List[str]:
        """Devuelve tips rápidos aleatorios"""
        tips = [
            "💡 Usa F2 para buscar productos rápidamente",
            "⚡ Presiona F3 para ir directo al pago",
            "🔍 Usa * en las búsquedas para encontrar coincidencias parciales",
            "🎯 El escáner de códigos de barras funciona en cualquier campo de búsqueda",
            "📊 F5 te muestra los reportes más importantes",
            "💾 Ctrl+S guarda cambios en cualquier formulario",
            "🔄 Esc cancela la operación actual",
            "🖨️ Ctrl+P imprime el ticket o reporte actual"
        ]
        
        import random
        return random.sample(tips, min(3, len(tips)))
    
    def search_help(self, search_term: str) -> List[Dict[str, Any]]:
        """Busca en toda la base de conocimientos"""
        results = []
        search_term = search_term.lower()
        
        # Buscar en FAQ
        for question, answer in self.knowledge_base["preguntas_frecuentes"].items():
            if search_term in question.lower() or search_term in answer.lower():
                results.append({
                    "type": "faq",
                    "title": question,
                    "content": answer,
                    "relevance": 0.9
                })
        
        # Buscar en funciones básicas
        for func_name, func_data in self.knowledge_base["funciones_basicas"].items():
            if search_term in func_name or search_term in func_data["descripcion"].lower():
                results.append({
                    "type": "function",
                    "title": func_name.replace("_", " ").title(),
                    "content": func_data["descripcion"],
                    "details": func_data,
                    "relevance": 0.8
                })
        
        # Buscar en atajos
        for shortcut, description in self.knowledge_base["atajos_teclado"].items():
            if search_term in shortcut.lower() or search_term in description.lower():
                results.append({
                    "type": "shortcut",
                    "title": f"Atajo: {shortcut}",
                    "content": description,
                    "relevance": 0.7
                })
        
    def get_engine_status(self) -> Dict[str, Any]:
        """Devuelve el estado de todos los engines"""
        status = {
            "active_engines": self.active_engines,
            "chatterbot_available": CHATTERBOT_AVAILABLE and hasattr(self, 'chatbot'),
            "transformers_available": TRANSFORMERS_AVAILABLE and hasattr(self, 'qa_pipeline'),
            "ollama_available": OLLAMA_AVAILABLE and hasattr(self, 'ollama_client'),
            "llama_api_available": self.config["use_llama_api"],
            "total_conversations": len(self.conversation_history) // 2,
            "last_engine_used": self.conversation_history[-1].get("engine_used") if self.conversation_history else None
        }
        
        # Información adicional de Ollama si está disponible
        if status["ollama_available"]:
            ollama_status = self.ollama_client.get_status()
            status.update({
                "ollama_healthy": ollama_status["healthy"],
                "ollama_current_model": ollama_status["current_model"],
                "ollama_models_count": ollama_status["total_models"],
                "ollama_models": ollama_status["available_models"]
            })
        
        return status
    
    def train_with_conversation(self, question: str, correct_answer: str):
        """Entrena el sistema con nuevas conversaciones"""
        if hasattr(self, 'chatbot'):
            trainer = ListTrainer(self.chatbot)
            trainer.train([question, correct_answer])
            
        # También agregarlo a la knowledge base temporal
        if "custom_qa" not in self.knowledge_base:
            self.knowledge_base["custom_qa"] = {}
        self.knowledge_base["custom_qa"][question] = correct_answer
    
    def get_conversation_analytics(self) -> Dict[str, Any]:
        """Obtiene analytics de las conversaciones"""
        if not self.conversation_history:
            return {"total_questions": 0}
        
        user_messages = [msg for msg in self.conversation_history if msg["type"] == "user"]
        assistant_messages = [msg for msg in self.conversation_history if msg["type"] == "assistant"]
        
        # Engines más usados
        engine_usage = {}
        for msg in assistant_messages:
            engine = msg.get("engine_used", "unknown")
            engine_usage[engine] = engine_usage.get(engine, 0) + 1
        
        # Preguntas más comunes (palabras clave)
        all_questions = " ".join([msg["question"] for msg in user_messages]).lower()
        common_words = {}
        for word in all_questions.split():
            if len(word) > 3:  # Ignorar palabras muy cortas
                common_words[word] = common_words.get(word, 0) + 1
        
        return {
            "total_questions": len(user_messages),
            "total_responses": len(assistant_messages),
            "engine_usage": engine_usage,
            "most_used_engine": max(engine_usage.items(), key=lambda x: x[1])[0] if engine_usage else None,
            "common_keywords": sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:10],
            "last_hour_questions": len([
                msg for msg in user_messages 
                if (datetime.now() - datetime.fromisoformat(msg["timestamp"])).seconds < 3600
            ])
        }
    
    def suggest_improvements(self) -> List[str]:
        """Sugiere mejoras basadas en el uso"""
        suggestions = []
        analytics = self.get_conversation_analytics()
        
        if analytics["total_questions"] == 0:
            return ["🎯 ¡Empieza preguntando algo! Por ejemplo: '¿Cómo hacer una venta?'"]
        
        # Analizar engines más usados
        if analytics.get("most_used_engine") == "rules":
            suggestions.append("🤖 Considera instalar ChatterBot para respuestas más naturales: pip install chatterbot")
        
        if "transformers" not in self.active_engines:
            suggestions.append("🧠 Para análisis avanzado instala: pip install transformers torch")
        
        if not self.config["use_llama_api"]:
            suggestions.append("🚀 Para respuestas más detalladas, configura Llama API local")
        
        # Palabras clave comunes
        common_keywords = dict(analytics.get("common_keywords", []))
        if "error" in common_keywords:
            suggestions.append("⚠️ Hay muchas consultas sobre errores. Revisa logs del sistema")
        
        if "producto" in common_keywords:
            suggestions.append("📦 Considera crear tutoriales visuales para gestión de productos")
        
        return suggestions[:5]  # Máximo 5 sugerencias
    
    def export_conversation_history(self, format: str = "json") -> Union[str, Dict]:
        """Exporta el historial de conversaciones"""
        if format == "json":
            return {
                "export_date": datetime.now().isoformat(),
                "total_conversations": len(self.conversation_history) // 2,
                "history": self.conversation_history,
                "analytics": self.get_conversation_analytics()
            }
        elif format == "txt":
            lines = ["=== HISTORIAL DE CONVERSACIONES POS AI ===\n"]
            for msg in self.conversation_history:
                timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                if msg["type"] == "user":
                    lines.append(f"[{timestamp}] USUARIO: {msg['question']}")
                else:
                    engine = msg.get("engine_used", "unknown")
                    lines.append(f"[{timestamp}] ASISTENTE ({engine}): {msg['response'].get('answer', 'N/A')}")
                lines.append("")
            return "\n".join(lines)
        
        return self.conversation_history
