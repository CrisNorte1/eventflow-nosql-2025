from fastapi import FastAPI
from pydantic import BaseModel
from reservas_pagos_service.chain import *

app = FastAPI(title="Servicio de Reservas y Pagos - EventFlow")

class ReservaRequest(BaseModel):
    evento_id: str
    email: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/reservar")
def reservar(body: ReservaRequest): 
    chain = ValidadorDatos( # Chain of Responsibility 
                ValidadorInventario(
                    ConfirmadorReserva()
                ))
    req = SolicitudReserva(evento_id=body.evento_id, email=body.email)
    result = chain.handle(req)
    return result
