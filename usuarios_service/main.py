from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import List

from usuarios_service.database import usuarios_col

app = FastAPI(title="Servicio de Usuarios - EventFlow")

class Usuario(BaseModel):
    tipo_documento: str
    nro_documento: str
    nombre: str
    apellido: str
    email: EmailStr
    historial_compras: List[str] = Field(default_factory=list)


@app.get("/health") # Endpoint de health check
def health():
    return {"status": "ok"}

@app.post("/api/usuarios", status_code=status.HTTP_201_CREATED) # Endpoint para crear un nuevo usuario
def crear_usuario(usuario: Usuario):
    if usuarios_col.find_one({"email": usuario.email}):
        raise HTTPException(status_code=409, detail="Email ya registrado")
    usuarios_col.insert_one(usuario.dict())
    return {"mensaje": "Usuario creado con exito"}

@app.get("/api/usuarios/{email}") # Endpoint para obtener un usuario por email
def obtener_usuario(email: str):
    usuario = usuarios_col.find_one({"email": email}, {"_id": 0})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario
