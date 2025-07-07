from sqlalchemy.orm import Session
from models.registro import Registro
from schemas.registro import RegistroCreate

def crear_registro(db: Session, registro: RegistroCreate):
    nuevo = Registro(**registro.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def obtener_registros(db: Session):
    return db.query(Registro).all()

def eliminar_registro(db: Session, id: int):
    r = db.query(Registro).filter(Registro.id == id).first()
    if r:
        db.delete(r)
        db.commit()
        return True
    return False