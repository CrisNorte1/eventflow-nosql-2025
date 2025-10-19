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
| **Reservas y Pagos** | Orquesta el proceso de compra, validaciones y pagos. | ⚡ **Redis** |

### 🧱 Justificación del Diseño

- **MongoDB** se eligió para *Usuarios* y *Eventos* por su estructura flexible y alto rendimiento en consultas de lectura.  
  Permite almacenar documentos JSON con diferentes campos según el tipo de usuario o evento.  
- **Redis** se usa en *Reservas y Pagos* por su velocidad y atomicidad para operaciones de reserva y bloqueo temporal de entradas.  
- Se adopta una estrategia **políglota**, usando distintas bases según la naturaleza del dato.
- La lectura de usuarios y eventos prioriza **disponibilidad y escalabilidad**, aceptando **consistencia eventual**.  
- Las reservas y pagos priorizan **consistencia fuerte**: una transacción debe confirmar o deshacer por completo.

