from abc import ABC, abstractmethod
from reservas_pagos_service.infra import redis_client, eventos_col, get_evento_http, get_usuario_http

LOCK_TTL_SECONDS = 60 # Tiempo de vida del lock en segundos

class SolicitudReserva: # Es el request que se pasa por la cadena
    def __init__(self, evento_id: str, email: str):
        self.evento_id = evento_id
        self.email = email

class Handler(ABC): # Handler base para la cadena de responsabilidad
    def __init__(self, next_handler=None):
        self.next = next_handler

    @abstractmethod
    def handle(self, req: SolicitudReserva): # Abstracto, se implementa en subclases
        pass

    def next_handle(self, req: SolicitudReserva): # Llama al siguiente handler si existe
        if self.next:
            return self.next.handle(req)
        return {"status": "ok"}

class ValidadorDatos(Handler): # Valida que los datos estén completos y el usuario exista
    def handle(self, req: SolicitudReserva):
        if not req.evento_id or not req.email:
            return {"status": "error", "reason": "Datos incompletos"}
        # Verificar que usuario exista (por REST)
        try:
            get_usuario_http(req.email)
        except Exception:
            return {"status": "error", "reason": "Usuario inexistente"}
        return self.next_handle(req)

class ValidadorInventario(Handler): # Valida que el evento exista y tenga disponibilidad
    def handle(self, req: SolicitudReserva):
        evt = eventos_col.find_one({"id": req.evento_id})
        if not evt:
            return {"status": "error", "reason": "Evento no existe"}
        if evt["entradas_disponibles"] <= 0:
            return {"status": "error", "reason": "Sin disponibilidad"}

        # Establecemos lock en Redis para evitar dobles reservas concurrentes
        lock_key = f"lock:evt:{req.evento_id}" # formateamos la clave del lock "lock:evt:<evento_id>"
        locked = redis_client.set(lock_key, req.email, nx=True, ex=LOCK_TTL_SECONDS) # Intentamos obtener el lock
        if not locked: # Si no se pudo obtener el lock para el evento que se está reservando
            return {"status": "error", "reason": "Evento bloqueado, intente nuevamente"}

        # Guardamos la clave de lock en el request (para liberar/compensar)
        req.lock_key = lock_key
        return self.next_handle(req)

class ProcesadorPago(Handler):
    def handle(self, req: SolicitudReserva):
        pago_exitoso = True # Asumimos que el pago es exitoso
        if not pago_exitoso: # Simulamos un pago fallido
            if hasattr(req, "lock_key"): # Si hay lock, lo liberamos
                redis_client.delete(req.lock_key)
            return {"status": "error", "reason": "Pago rechazado"}
        return self.next_handle(req) # Continuamos al siguiente handler

class ConfirmadorReserva(Handler):
    def handle(self, req: SolicitudReserva):
        result = eventos_col.update_one(
            {"id": req.evento_id, "entradas_disponibles": {"$gt": 0}}, # Se asegura que haya disponibilidad
            {"$inc": {"entradas_disponibles": -1}} # Resta en 1 las entradas disponibles
        )
        if result.modified_count != 1: # Si no se modificó nada, significa que no se pudo reservar
            if hasattr(req, "lock_key"):
                redis_client.delete(req.lock_key) # liberar el lock
            return {"status": "error", "reason": "No se pudo confirmar (competencia)"}

        # liberar el lock (o dejar que expire)
        if hasattr(req, "lock_key"):
            redis_client.delete(req.lock_key)

        return {"status": "ok", "mensaje": "Reserva confirmada"}
