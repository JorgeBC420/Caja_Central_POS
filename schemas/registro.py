from pydantic import BaseModel
from datetime import datetime

class RegistroBase(BaseModel):
    descripcion: str
    monto: float
    tipo: str

class RegistroCreate(RegistroBase):
    pass

class RegistroOut(RegistroBase):
    id: int
    fecha: datetime

    class Config:
        orm_mode = True