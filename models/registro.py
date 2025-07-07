from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Registro(Base):
    __tablename__ = "registros"
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    tipo = Column(String, nullable=False)
    fecha = Column(DateTime, default=datetime.now)