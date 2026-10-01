---
tipo: concepto
titulo: "Tenant"
alias: [cliente, negocio]
creado: 2026-10-01
actualizado: 2026-10-01
---

# Tenant

## Definicion
Un negocio que compra el sistema. Tiene su propio docker compose project con red, volumen, BD y secretos aislados en la VM compartida.

## Por que importa en este proyecto
Aislamiento: un ban, una fuga o una caída de un cliente no afecta a otro (Agent Engine A4/A5 [INT:D:/Dataseed/Agent Engine/CONSTITUCION.md]).

## Se relaciona con
[[Rubro]] · [[Takeover]]

## Aparece en
[[ADR-003]]
