from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from reservas_pagos_service.infra import (
    redis_client,
    eventos_col,
    usuarios_col,
    get_usuario_http,
)
from reservas_pagos_service.saga import Saga, SagaError, SagaStep

LOCK_TTL_SECONDS = 60  # Tiempo de vida del lock en segundos


@dataclass
class SolicitudReserva:
    evento_id: str
    email: str
    lock_key: Optional[str] = None


class Handler(ABC):  # Handler base para la cadena de responsabilidad
    def __init__(self, next_handler=None):
        self.next = next_handler

    @abstractmethod
    def handle(self, req: SolicitudReserva):  # Maneja la solicitud de reserva
        raise NotImplementedError

    def next_handle(self, req: SolicitudReserva):  # Llama al siguiente handler si existe
        if self.next:
            return self.next.handle(req)
        return {"status": "ok"}


class ValidadorDatos(Handler):  # Valida que los datos de la solicitud sean correctos
    def handle(self, req: SolicitudReserva):
        if not req.evento_id or not req.email:
            return {"status": "error", "reason": "Datos incompletos"}
        try:
            get_usuario_http(req.email)
        except Exception:
            return {"status": "error", "reason": "Usuario inexistente"}
        return self.next_handle(req)


class ValidadorInventario(Handler):  # Valida que haya inventario disponible y bloquea el evento
    def handle(self, req: SolicitudReserva):
        evt = eventos_col.find_one({"id": req.evento_id})
        if not evt:
            return {"status": "error", "reason": "Evento no existe"}
        if evt["entradas_disponibles"] <= 0:
            return {"status": "error", "reason": "Sin disponibilidad"}

        lock_key = f"lock:evt:{req.evento_id}"  # Lock para el evento
        locked = redis_client.set(lock_key, req.email, nx=True, ex=LOCK_TTL_SECONDS)  # Si existe, no lo bloquea
        if not locked:  # Si existe el lock, otro proceso lo esta manejando
            return {"status": "error", "reason": "Evento bloqueado, intente nuevamente"}

        req.lock_key = lock_key
        return self.next_handle(req)


class ReservaSagaContext:
    def __init__(self, solicitud: SolicitudReserva):
        self.solicitud = solicitud
        self.pago_confirmado = False
        self.inventario_actualizado = False
        self.historial_actualizado = False


class ConfirmadorReserva(Handler):  # Confirma la reserva usando una saga
    def handle(self, req: SolicitudReserva):
        context = ReservaSagaContext(req)
        saga = Saga(
            [
                SagaStep( # Paso de la saga
                    "procesar_pago",
                    self._procesar_pago,
                    self._compensar_pago,
                ),
                SagaStep(
                    "descontar_inventario",
                    self._descontar_inventario,
                    self._restaurar_inventario,
                ),
                SagaStep(
                    "actualizar_historial",
                    self._registrar_historial,
                    self._revertir_historial,
                ),
            ]
        )

        try:
            saga.execute(context)
            return {"status": "ok", "mensaje": "Reserva confirmada"}
        except SagaError as err:
            return {"status": "error", "reason": err.reason}
        finally:
            if req.lock_key:
                redis_client.delete(req.lock_key)

    @staticmethod
    def _procesar_pago(ctx: ReservaSagaContext):
        # No vamos a implementar un pago real porque es un monton; simulamos exito
        ctx.pago_confirmado = True

    @staticmethod
    def _compensar_pago(ctx: ReservaSagaContext):
        if ctx.pago_confirmado:
            # Lo mismo, simulamos la compensacion
            ctx.pago_confirmado = False

    @staticmethod
    def _descontar_inventario(ctx: ReservaSagaContext):  # Descuenta una entrada del inventario
        solicitud = ctx.solicitud
        result = eventos_col.update_one(
            {"id": solicitud.evento_id, "entradas_disponibles": {"$gt": 0}},  # Verifica que haya entradas disponibles
            {"$inc": {"entradas_disponibles": -1}},
        )
        if result.modified_count != 1:
            raise SagaError("No se pudo confirmar (competencia)")
        ctx.inventario_actualizado = True  # Marca que se actualizo el inventario

    @staticmethod
    def _restaurar_inventario(ctx: ReservaSagaContext):  # Restaura una entrada al inventario
        if ctx.inventario_actualizado:
            eventos_col.update_one(
                {"id": ctx.solicitud.evento_id},
                {"$inc": {"entradas_disponibles": 1}},
            )
            ctx.inventario_actualizado = False

    @staticmethod
    def _registrar_historial(ctx: ReservaSagaContext):  # Actualiza el historial de compras del usuario
        solicitud = ctx.solicitud
        resultado = usuarios_col.update_one(
            {"email": solicitud.email},
            {"$push": {"historial_compras": solicitud.evento_id}},
        )
        if resultado.modified_count != 1:
            raise SagaError("No se pudo actualizar el historial")
        ctx.historial_actualizado = True # Marca que se actualizo el historial

    @staticmethod
    def _revertir_historial(ctx: ReservaSagaContext): # Revierte la actualizacion del historial de compras
        if ctx.historial_actualizado:
            usuarios_col.update_one(
                {"email": ctx.solicitud.email},
                {"$pull": {"historial_compras": ctx.solicitud.evento_id}},
            )
            ctx.historial_actualizado = False  # Marca que se revirtio el historial
            
