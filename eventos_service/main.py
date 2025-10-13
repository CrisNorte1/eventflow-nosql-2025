from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from eventos_service.database import eventos_col

app = FastAPI(title="Servicio de Eventos - EventFlow")

class Evento(BaseModel):
    id: str
    nombre: str
    fecha: str        # simplificado (ISO string). Luego podés usar datetime
    lugar: str
    aforo_total: int
    entradas_disponibles: int

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/eventos", status_code=status.HTTP_201_CREATED)
def crear_evento(evt: Evento):
    if eventos_col.find_one({"id": evt.id}):
        raise HTTPException(status_code=409, detail="Evento ya existe")
    if evt.entradas_disponibles > evt.aforo_total:
        raise HTTPException(status_code=400, detail="Disponibles > aforo")
    eventos_col.insert_one(evt.dict())
    return {"mensaje": "Evento creado"}

@app.get("/api/eventos/{evento_id}")
def obtener_evento(evento_id: str):
    evt = eventos_col.find_one({"id": evento_id}, {"_id": 0})
    if not evt:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evt
