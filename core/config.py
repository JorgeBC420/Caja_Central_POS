import sqlite3

DB_NAME = 'caja_registradora_pos_cr.db'
DEFAULT_USER = {'username': 'admin', 'password': 'admin123'}
API_BASE_URL = "https://tu-api-central.com/api"
DEFAULT_IVA_RATE = 0.13
DEFAULT_REGIMEN_EMISOR = 'tradicional'

class ConfigManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self._initialize_db()  # <-- Asegura que la tabla existe al iniciar
        self.config = self._load_config_from_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _initialize_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuraciones (
                    clave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
                )
            """)

    def _load_config_from_db(self):
        config = {}
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT clave, valor FROM configuraciones")
                for clave, valor in cursor.fetchall():
                    if clave == 'tasa_iva_general':
                        config['tasa_iva'] = float(valor)
                    elif clave == 'regimen_emisor':
                        config['regimen_emisor'] = valor
                    elif clave == 'tasa_dolar':
                        config['tasa_dolar'] = float(valor)
        except sqlite3.OperationalError as e:
            print("Error al cargar configuración:", e)
            self._initialize_db()
            # Intentar recargar después de crear la tabla
            return self._load_config_from_db()
        if 'tasa_iva' not in config:
            config['tasa_iva'] = DEFAULT_IVA_RATE
        if 'regimen_emisor' not in config:
            config['regimen_emisor'] = DEFAULT_REGIMEN_EMISOR
        if 'tasa_dolar' not in config:
            config['tasa_dolar'] = 560.0
        return config
    def _initialize_db(self):
        """Inicializa la base de datos y crea la tabla de configuraciones si no existe."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuraciones (
                    clave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
                )
            """)

    def update_config(self, key, value):
        """Actualiza la configuración en memoria y en la base de datos."""
        db_key = {
            'tasa_iva': 'tasa_iva_general',
            'regimen_emisor': 'regimen_emisor',
            'tasa_dolar': 'tasa_dolar'
        }.get(key, key)
        self.config[key] = value
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE configuraciones SET valor=? WHERE clave=?",
                (str(value), db_key)
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO configuraciones (clave, valor) VALUES (?, ?)",
                    (db_key, str(value))
                )
            conn.commit()
        return True

    def reset_to_initial_config(self):
        """Restaura la configuración a los valores iniciales en la base de datos."""
        self.update_config('tasa_iva', DEFAULT_IVA_RATE)
        self.update_config('regimen_emisor', DEFAULT_REGIMEN_EMISOR)
        self.update_config('tasa_dolar', 560.0)
        self.config = self._load_config_from_db()

    def add_config_key(self, key, value):
        """Agrega una nueva clave de configuración si no existe."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM configuraciones WHERE clave=?", (key,))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO configuraciones (clave, valor) VALUES (?, ?)",
                    (key, str(value))
                )
                conn.commit()
                self.config[key] = value
                return True
            else:
                return False