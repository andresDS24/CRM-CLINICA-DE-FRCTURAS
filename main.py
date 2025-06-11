from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, engine, Base
import models, schemas
from typing import List
from datetime import date, timedelta

Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/aseguradoras/", response_model=schemas.Aseguradora)
def crear_aseguradora(aseg: schemas.AseguradoraCreate, db: Session = Depends(get_db)):
    db_aseg = models.Aseguradora(**aseg.dict())
    db.add(db_aseg)
    db.commit()
    db.refresh(db_aseg)
    return db_aseg

@app.get("/aseguradoras/", response_model=List[schemas.Aseguradora])
def listar_aseguradoras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Aseguradora).offset(skip).limit(limit).all()

@app.post("/contratos/", response_model=schemas.Contrato)
def crear_contrato(cont: schemas.ContratoCreate, db: Session = Depends(get_db)):
    db_contrato = models.Contrato(**cont.dict())
    db.add(db_contrato)
    db.commit()
    db.refresh(db_contrato)
    return db_contrato

@app.get("/contratos/", response_model=List[schemas.Contrato])
def listar_contratos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Contrato).offset(skip).limit(limit).all()

@app.get("/informes/total-por-aseguradora/")
def total_por_aseguradora(db: Session = Depends(get_db)):
    return db.query(
        models.Aseguradora.nombre,
        func.count(models.Contrato.id).label("total_contratos"),
        func.sum(models.Contrato.techo_mensual).label("total_techo")
    ).join(models.Contrato).group_by(models.Aseguradora.nombre).all()

@app.get("/informes/vencimientos-proximos/")
def vencimientos_proximos(db: Session = Depends(get_db)):
    hoy = date.today()
    limite = hoy + timedelta(days=30)
    return db.query(models.Contrato).filter(models.Contrato.fecha_fin <= limite).all()
