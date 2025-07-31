from schemas.registro import RegistroCreate
from services import db, registro
from sqlalchemy.orm import Session

def get_db():
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()

def registrar_ingreso(descripcion, monto, tipo="Ingreso"):
    with next(get_db()) as session:
        r = RegistroCreate(descripcion=descripcion, monto=monto, tipo=tipo)
        return registro.crear_registro(session, r)

def ver_historial():
    with next(get_db()) as session:
        return registro.obtener_registros(session)

def eliminar(id):
    with next(get_db()) as session:
        return registro.eliminar_registro(session, id)