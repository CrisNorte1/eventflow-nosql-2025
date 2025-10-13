from pydantic import BaseModel
from typing import List, Optional

class Usuario(BaseModel):
    tipo_documento: str
    nro_documento: str
    nombre: str
    apellido: str
    email: str
    historial_compras: Optional[List[str]] = []
