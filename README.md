# ���� EventFlow ��� Plataforma de Gesti+�n de Eventos (Tarea 2 ��� NoSQL 2025)

## ���� Descripci+�n General

**EventFlow** es una plataforma ficticia para la **gesti+�n y venta de entradas de eventos**, dise+�ada con una **arquitectura de microservicios**.  
El objetivo del proyecto es aplicar conceptos de **bases de datos NoSQL**, **consistencia distribuida**, **escalabilidad** y **patrones de dise+�o** (SAGA y Chain of Responsibility).

---

## ���� Arquitectura General

El sistema se compone de tres microservicios principales:

| Microservicio | Responsabilidad | Base de Datos |
|----------------|----------------|----------------|
| **Usuarios** | Maneja los perfiles de usuario y su historial de compras. | ���䴩� **MongoDB** |
| **Eventos** | Administra los eventos, fechas, lugares y entradas disponibles. | ���䴩� **MongoDB** |
| **Reservas y Pagos** | Orquesta el proceso de compra, validaciones y pagos. | ��� **Redis** + MongoDB |

### ���� Justificaci+�n del Dise+�o

- **MongoDB** se eligi+� para *Usuarios* y *Eventos* por su estructura flexible y alto rendimiento en consultas de lectura.  
  Permite almacenar documentos JSON con diferentes campos seg+�n el tipo de usuario o evento.  
- **Redis** se usa en *Reservas y Pagos* por su velocidad y atomicidad para operaciones de reserva y bloqueo temporal de entradas.  
- Se adopta una estrategia **pol+�glota**, usando distintas bases seg+�n la naturaleza del dato.
- La lectura de usuarios y eventos prioriza **disponibilidad y escalabilidad**, aceptando **consistencia eventual**.  
- Las reservas y pagos priorizan **consistencia fuerte**: una transacci+�n debe confirmar o deshacer por completo.

---

## ���� Diagrama de Arquitectura

    ������������������������������������������������������������������������          ������������������������������������������������
    ���   Servicio Usuarios  ��� ���������������������������   MongoDB    ���
    ������������������������������������������������������������������������          ������������������������������������������������
               ���
               ��� (HTTP REST)
               ��+
    ������������������������������������������������������������������������         ������������������������������������������������
    ���   Servicio Eventos   ������������������������������   MongoDB    ���
    ������������������������������������������������������������������������         ������������������������������������������������
               ���
               ��� (Orquestaci+�n SAGA)
               ��+
    ���������������������������������������������������������������������������������������������������������������������������������������������������������������������������         ������������������������������������������������������
    ���  Servicio Reservas y Pagos                            ������������������������������   Redis (lock) ���
    ���  (SAGA + Chain of Responsibility)                     ���         ������������������������������������������������������
    ���        ���                                              ���
    ���        ������������������������ Actualiza disponibilidad en MongoDB  ���
    ���������������������������������������������������������������������������������������������������������������������������������������������������������������������������

---

## ���� Patr+�n SAGA (Orquestada)

El patr+�n **SAGA** coordina una transacci+�n distribuida que involucra varios microservicios (Usuarios, Eventos y Pagos).  
En este caso, el **Servicio de Reservas y Pagos** act+�a como **Orquestador** central.

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
   - Se ejecuta la **compensaci+�n** ��� borrar el lock (`DEL`).

### Compensaci+�n (Rollback)

La acci+�n compensatoria de la SAGA consiste en eliminar el candado (`lock`) en Redis,  
liberando el asiento y manteniendo la consistencia final del sistema.

---

## ��ִ�� Patr+�n Chain of Responsibility

Dentro del servicio de **Reservas y Pagos**, la l+�gica de negocio se estructura como una cadena de manejadores (`Handlers`):


Cada manejador realiza una validaci+�n o acci+�n:
- **ValidadorDatos:** Comprueba campos y existencia del usuario.  
- **ValidadorInventario:** Verifica disponibilidad y aplica lock en Redis.  
- **ProcesadorPago:** Simula cobro.  
- **ConfirmadorReserva:** Confirma la reserva en MongoDB y libera el lock.

La cadena se detiene si alguno de los pasos falla, evitando efectos secundarios innecesarios.

---

## ���� Patr+�n SAGA dentro del Chain

El **SAGA est+� embebido en la Chain of Responsibility**.  
Cada manejador es un paso de la transacci+�n distribuida y define su acci+�n compensatoria (borrar el lock si falla).  
Esto combina **orquestaci+�n SAGA** con una **implementaci+�n modular y extensible**.

---

## ���� Modelado de Datos (NoSQL)

### ���� Colecci+�n Usuarios (MongoDB)
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

### ���� Colecci+�n Usuarios (MongoDB)
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
### ���� Ejecuci+�n del Proyecto
1������ Levantar MongoDB y Redis con Docker
```bash
docker-compose up -d
```
2������ Activar entorno virtual
```bash
venv\Scripts\activate
```
3������ Ejecutar los microservicios
```bash
# Usuarios
uvicorn usuarios_service.main:app --reload --port 8001

# Eventos
uvicorn eventos_service.main:app --reload --port 8002

# Reservas y Pagos
uvicorn reservas_pagos_service.main:app --reload --port 8003
```
4������ Probar endpoints
| Servicio         | URL Swagger                                              |
| ---------------- | -------------------------------------------------------- |
| Usuarios         | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |
| Eventos          | [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs) |
| Reservas y Pagos | [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs) |
### 🧪 Pruebas con Apache JMeter

- En la raíz del repositorio encontrarás **View Results Tree.jmx** con un plan básico para validar el flujo feliz de reservas.
- Ábrelo en Apache JMeter 5.6.3, ajusta URLs si cambiaste puertos y ejecuta la prueba para observar la respuesta `{"status":"ok","mensaje":"Reserva confirmada"}`.
- Se recomienda duplicar el escenario agregando casos negativos (sin stock, usuario inexistente) para mostrar la compensación automática de la Saga.


���� Integrantes

Cristian Norte
Santiago Iroldi

���� Fecha de entrega

10 de noviembre de 2025
* * *
# Opcionales
## Opcional 4 - Event Sourcing y CQRS


**Event Sourcing (ES):** En lugar de almacenar el estado actual de una entidad (ej. "entradas_disponibles: 50"), se almacenan todos los eventos que la afectaron (ej. "ReservaCreada", "PagoProcesado", "ReservaCancelada"). El estado actual se reconstruye aplicando estos eventos en secuencia. Esto permite auditor+�a completa, reconstrucci+�n hist+�rica y resiliencia.

**CQRS (Command Query Responsibility Segregation):**  Separa las operaciones de escritura (comandos) de las de lectura (queries). Los comandos cambian el estado (escriben eventos), las queries leen vistas optimizadas (proyecciones). Esto mejora escalabilidad y rendimiento en sistemas de alta carga.

### Escenario Beneficioso en EventFlow
Estos patrones se podr+�an aplicar  para el Servicio de Reservas y Pagos porque:

**Auditor+�a:** Con event sourcing se podr+�a rastrear cada reserva/opago Necesitas para evitar fraudes, resolver disputas o cumplir regulaciones que exigan trazabilidad de las transacciones. Event Sourcing nosm permitir+�a reconstruir el historial completo de un evento o usuario.
**An+�lisis y Reportes:** Para metricas como patrones de compra por evento o tasa de conversi+�n de reservas, CQRS permite queries optimizadas sin afectar el rendimiento de escrituras cr+�ticas.

**Escalabilidad:** Las lecturas (ej: consultar las entradas disponibles de un evento X) pueden ser mucho m+�s frecuentes que las escrituras (reservas). Con CQRS podr+�anmos escalar nodos de lecturas independientemente sin afectar la escritura.

**Consistencia Eventual:** Alinea con los requerimientos de consistencia eventual para lecturas r+�pidas, mientras mantiene consistencia fuerte en escrituras (reservas +�nicas).


**Diferencia con la Soluci+�n Actual (MongoDB + Redis):** Actualmente, MongoDB almacena el estado mutable (ej. entradas_disponibles), y Redis maneja locks temporales. Esto es simple pero limita la auditor+�a (no hay historial de cambios) y puede tener problemas de consistencia en fallos. Con ES/CQRS, tendr+�as un event store inmutable para todas las transacciones, y proyecciones separadas para lecturas. Redis seguir+�a para locks temporales, pero el estado se derivar+�a de eventos.

