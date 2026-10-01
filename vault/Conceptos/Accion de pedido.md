---
tipo: concepto
titulo: "Accion de pedido"
alias: [accion por rubro]
creado: 2026-10-01
actualizado: 2026-10-01
---

# Accion de pedido

## Definicion
Escritura que cierra una venta, con una máquina de estados única preparar → confirmación del cliente → confirmar. Cambia solo el destino según el rubro: stock_decrement (BD), calendar_booking (Google Calendar) o registro. Idempotente y transaccional.

## Por que importa en este proyecto
El usuario lo definió así: en una tienda descuenta stock, en una peluquería agenda; el procedimiento es el mismo y solo cambia la tabla o la plataforma.

## Se relaciona con
[[Rubro]] · [[Capa SAS]]

## Aparece en
[[ADR-005]]
