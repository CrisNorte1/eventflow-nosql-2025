# 🌀 EventFlow – Plataforma de Gestión de Eventos (Tarea 2 – NoSQL 2025)

## 📘 Descripción General

**EventFlow** es una plataforma ficticia para la **gestión y venta de entradas de eventos**, diseñada con una **arquitectura de microservicios**.  
El objetivo del proyecto es aplicar conceptos de **bases de datos NoSQL**, **consistencia distribuida**, **escalabilidad** y **patrones de diseño** (SAGA y Chain of Responsibility).

---

## 🧩 Arquitectura General

El sistema se compone de tres microservicios principales:

| Microservicio | Responsabilidad | Base de Datos |
|----------------|----------------|----------------|
| **Usuarios** | Maneja los perfiles de usuario y su historial de compras. | 🗄️ **MongoDB** |
| **Eventos** | Administra los eventos, fechas, lugares y entradas disponibles. | 🗄️ **MongoDB** |
| **Reservas y Pagos** | Orquesta el proceso de compra, validaciones y pagos. | ⚡ **Redis** + MongoDB |

### 🧱 Justificación del Diseño

- **MongoDB** se eligió para *Usuarios* y *Eventos* por su estructura flexible y alto rendimiento en consultas de lectura.  
  Permite almacenar documentos JSON con diferentes campos según el tipo de usuario o evento.  
- **Redis** se usa en *Reservas y Pagos* por su velocidad y atomicidad para operaciones de reserva y bloqueo temporal de entradas.  
- Se adopta una estrategia **políglota**, usando distintas bases según la naturaleza del dato.
- La lectura de usuarios y eventos prioriza **disponibilidad y escalabilidad**, aceptando **consistencia eventual**.  
- Las reservas y pagos priorizan **consistencia fuerte**: una transacción debe confirmar o deshacer por completo.

---

## 🧭 Diagrama de Arquitectura

    ┌──────────────────────┐          ┌──────────────┐
    │   Servicio Usuarios  │ ◀──────▶│   MongoDB    │
    └──────────────────────┘          └──────────────┘
               │
               │ (HTTP REST)
               ▼
    ┌──────────────────────┐         ┌──────────────┐
    │   Servicio Eventos   │◀──────▶│   MongoDB    │
    └──────────────────────┘         └──────────────┘
               │
               │ (Orquestación SAGA)
               ▼
    ┌───────────────────────────────────────────────────────┐         ┌────────────────┐
    │  Servicio Reservas y Pagos                            │◀──────▶│   Redis (lock) │
    │  (SAGA + Chain of Responsibility)                     │         └────────────────┘
    │        │                                              │
    │        └──────▶ Actualiza disponibilidad en MongoDB  │
    └───────────────────────────────────────────────────────┘

---

## 🔄 Patrón SAGA (Orquestada)

El patrón **SAGA** coordina una transacción distribuida que involucra varios microservicios (Usuarios, Eventos y Pagos).  
En este caso, el **Servicio de Reservas y Pagos** actúa como **Orquestador** central.

### Flujo resumido:

1. El usuario inicia una reserva (`POST /api/reservar`).
2. El servicio orquestador valida que el usuario exista (**Usuarios**).
3. Consulta si el evento tiene cupos disponibles (**Eventos**).
4. Bloquea temporalmente el asiento en **Redis** (`SETNX` con TTL).
5. Procesa el pago (simulado).
6. Si todo sale bien:
   - Decrementa el aforo en MongoDB.
   - Elimina el lock en Redis.
7. Si algo falla en cualquier paso:
   - Se ejecuta la **compensación** → borrar el lock (`DEL`).

### Compensación (Rollback)

La acción compensatoria de la SAGA consiste en eliminar el candado (`lock`) en Redis,  
liberando el asiento y manteniendo la consistencia final del sistema.

---

## ⚙️ Patrón Chain of Responsibility

Dentro del servicio de **Reservas y Pagos**, la lógica de negocio se estructura como una cadena de manejadores (`Handlers`):


Cada manejador realiza una validación o acción:
- **ValidadorDatos:** Comprueba campos y existencia del usuario.  
- **ValidadorInventario:** Verifica disponibilidad y aplica lock en Redis.  
- **ProcesadorPago:** Simula cobro.  
- **ConfirmadorReserva:** Confirma la reserva en MongoDB y libera el lock.

La cadena se detiene si alguno de los pasos falla, evitando efectos secundarios innecesarios.

---

## 🧠 Patrón SAGA dentro del Chain

El **SAGA está embebido en la Chain of Responsibility**.  
Cada manejador es un paso de la transacción distribuida y define su acción compensatoria (borrar el lock si falla).  
Esto combina **orquestación SAGA** con una **implementación modular y extensible**.

---

## 🧩 Modelado de Datos (NoSQL)

### 📄 Colección Usuarios (MongoDB)
```json
{
  "_id": "uuid",
  "tipo_documento": "DNI",
  "nro_documento": "51234567",
  "nombre": "Cristian",
  "apellido": "Norte",
  "email": "cnorte@example.com",
  "historial_compras": ["id_reserva_1", "id_reserva_2"]
}
```

### 📄 Colección Usuarios (MongoDB)
```json
{
  "_id": "evt123",
  "nombre": "Concierto Arctic Monkeys",
  "fecha": "2025-11-10",
  "lugar": "Antel Arena",
  "aforo_total": 12000,
  "entradas_disponibles": 8500
}
```
### 🚀 Ejecución del Proyecto
1️⃣ Levantar MongoDB y Redis con Docker
```bash
docker-compose up -d
```
2️⃣ Activar entorno virtual
```bash
venv\Scripts\activate
```
3️⃣ Ejecutar los microservicios
```bash
# Usuarios
uvicorn usuarios_service.main:app --reload --port 8001

# Eventos
uvicorn eventos_service.main:app --reload --port 8002

# Reservas y Pagos
uvicorn reservas_pagos_service.main:app --reload --port 8003
```
4️⃣ Probar endpoints
| Servicio         | URL Swagger                                              |
| ---------------- | -------------------------------------------------------- |
| Usuarios         | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |
| Eventos          | [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs) |
| Reservas y Pagos | [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs) |
