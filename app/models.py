from fastapi import Depends, HTTPException
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from pydantic import BaseModel, ConfigDict
from typing import Optional

SQLALCHEMY_DATABASE_URL = "sqlite:///./talentcore.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Empleado(Base):
    __tablename__ = "empleados"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    rol = Column(String, nullable=False)
    anios_antiguedad = Column(Integer, nullable=False, default=1)
    manager_id = Column(Integer, ForeignKey("empleados.id"), nullable=True)

class SolicitudVacaciones(Base):
    __tablename__ = "solicitudes_vacaciones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    empleado_id = Column(Integer, ForeignKey("empleados.id"), nullable=False)
    dias_solicitados = Column(Integer, nullable=False)
    motivo = Column(String, nullable=True)
    estado = Column(String, nullable=False, default="PENDING")
    revisado_por_id = Column(Integer, ForeignKey("empleados.id"), nullable=True)

class EmpleadoCreate(BaseModel):
    nombre: str
    email: str
    rol: str
    anios_antiguedad: int
    manager_id: Optional[int] = None

class EmpleadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: str
    rol: str
    anios_antiguedad: int
    manager_id: Optional[int] = None

class SaldoResponse(BaseModel):
    empleado_id: int
    dias_totales: int
    dias_aprobados: int
    saldo_disponible: int

class SolicitudCreate(BaseModel):
    empleado_id: int
    dias_solicitados: int
    motivo: Optional[str] = None

class RevisionRequest(BaseModel):
    accion: str

class SolicitudResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empleado_id: int
    dias_solicitados: int
    motivo: Optional[str]
    estado: str
    revisado_por_id: Optional[int]
