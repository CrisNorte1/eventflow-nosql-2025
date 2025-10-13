from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from usuarios_service.database import usuarios_col

app = FastAPI(title="Servicio de Usuarios - EventFlow")

class Usuario(BaseModel):
    tipo_documento: str
    nro_documento: str
    nombre: str
    apellido: str
    email: str
    historial_compras: Optional[List[str]] = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/usuarios", status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: Usuario):
    if usuarios_col.find_one({"email": usuario.email}):
        raise HTTPException(status_code=409, detail="Email ya registrado")
    usuarios_col.insert_one(usuario.dict())
    return {"mensaje": "Usuario creado con éxito"}

@app.get("/api/usuarios/{email}")
def obtener_usuario(email: str):
    usuario = usuarios_col.find_one({"email": email}, {"_id": 0})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario
