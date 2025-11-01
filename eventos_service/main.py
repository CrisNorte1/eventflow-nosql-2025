from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from eventos_service.database import eventos_col

app = FastAPI(title="Servicio de Eventos - EventFlow")

class Evento(BaseModel):
    id: str
    nombre: str
    fecha: datetime
    lugar: str
    aforo_total: int = Field(..., gt=0) # Obligatorio y mayor que 0
    entradas_disponibles: int = Field(..., ge=0) # Obligatorio y mayor o igual que 0

@app.get("/health") # Endpoint de health check
def health():
    return {"status": "ok"}

@app.post("/api/eventos", status_code=status.HTTP_201_CREATED) # Endpoint para crear un nuevo evento
def crear_evento(evt: Evento):
    if eventos_col.find_one({"id": evt.id}):
        raise HTTPException(status_code=409, detail="Evento ya existe")
    if evt.entradas_disponibles > evt.aforo_total:
        raise HTTPException(status_code=400, detail="Disponibles mayores al aforo")

    evento_fecha = evt.fecha
    if evento_fecha.tzinfo: # Fecha con zona horaria
        fecha_ahora = datetime.now(evento_fecha.tzinfo) # fecha_ahora con zona horaria
    else:
        fecha_ahora = datetime.now() # fecha_ahora sin zona horaria

    if evento_fecha <= fecha_ahora: # La fecha del evento debe ser futura
        raise HTTPException(status_code=400, detail="La fecha del evento debe ser futura")

    eventos_col.insert_one(evt.dict())
    return {"mensaje": "Evento creado"}


@app.get("/api/eventos/{evento_id}")
def obtener_evento(evento_id: str):
    evt = eventos_col.find_one({"id": evento_id}, {"_id": 0})
    if not evt:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evt
