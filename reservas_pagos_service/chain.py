from abc import ABC, abstractmethod
from reservas_pagos_service.infra import redis_client, eventos_col, get_evento_http, get_usuario_http

LOCK_TTL_SECONDS = 60

class SolicitudReserva:
    def __init__(self, evento_id: str, email: str):
        self.evento_id = evento_id
        self.email = email

class Handler(ABC):
    def __init__(self, next_handler=None):
        self.next = next_handler

    @abstractmethod
    def handle(self, req: SolicitudReserva):
        pass

    def next_handle(self, req: SolicitudReserva):
        if self.next:
            return self.next.handle(req)
        return {"status": "ok"}

class ValidadorDatos(Handler):
    def handle(self, req: SolicitudReserva):
        if not req.evento_id or not req.email:
            return {"status": "error", "reason": "Datos incompletos"}
        # Verificar que usuario exista (por REST)
        try:
            get_usuario_http(req.email)
        except Exception:
            return {"status": "error", "reason": "Usuario inexistente"}
        return self.next_handle(req)

class ValidadorInventario(Handler):
    def handle(self, req: SolicitudReserva):
        evt = eventos_col.find_one({"id": req.evento_id})
        if not evt:
            return {"status": "error", "reason": "Evento no existe"}
        if evt["entradas_disponibles"] <= 0:
            return {"status": "error", "reason": "Sin disponibilidad"}

        # Lock en Redis para evitar dobles reservas concurrentes
        lock_key = f"lock:evt:{req.evento_id}"
        locked = redis_client.set(lock_key, req.email, nx=True, ex=LOCK_TTL_SECONDS)
        if not locked:
            return {"status": "error", "reason": "Evento bloqueado, intente nuevamente"}

        # Guardamos la clave de lock en el request (para liberar/compensar)
        req.lock_key = lock_key
        return self.next_handle(req)

class ProcesadorPago(Handler):
    def handle(self, req: SolicitudReserva):
        pago_exitoso = True
        if not pago_exitoso:
            if hasattr(req, "lock_key"):
                redis_client.delete(req.lock_key)
            return {"status": "error", "reason": "Pago rechazado"}
        return self.next_handle(req)

class ConfirmadorReserva(Handler):
    def handle(self, req: SolicitudReserva):
        result = eventos_col.update_one(
            {"id": req.evento_id, "entradas_disponibles": {"$gt": 0}},
            {"$inc": {"entradas_disponibles": -1}}
        )
        if result.modified_count != 1:
            if hasattr(req, "lock_key"):
                redis_client.delete(req.lock_key)
            return {"status": "error", "reason": "No se pudo confirmar (competencia)"}

        # liberar el lock (o dejar que expire)
        if hasattr(req, "lock_key"):
            redis_client.delete(req.lock_key)

        return {"status": "ok", "mensaje": "Reserva confirmada"}
