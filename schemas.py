from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class ContratoBase(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    tipo_tarifa: str
    techo_mensual: float
    condiciones: Optional[str]
    aseguradora_id: int

class ContratoCreate(ContratoBase): pass

class Contrato(ContratoBase):
    id: int
    class Config:
        orm_mode = True

class AseguradoraBase(BaseModel):
    nombre: str
    nit: str
    contacto: str

class AseguradoraCreate(AseguradoraBase): pass

class Aseguradora(AseguradoraBase):
    id: int
    contratos: List[Contrato] = []
    class Config:
        orm_mode = True
