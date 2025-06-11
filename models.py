from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Aseguradora(Base):
    __tablename__ = "aseguradoras"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    nit = Column(String)
    contacto = Column(String)
    contratos = relationship("Contrato", back_populates="aseguradora")

class Contrato(Base):
    __tablename__ = "contratos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    tipo_tarifa = Column(String)
    techo_mensual = Column(Float)
    condiciones = Column(Text)
    aseguradora_id = Column(Integer, ForeignKey("aseguradoras.id"))
    aseguradora = relationship("Aseguradora", back_populates="contratos")
