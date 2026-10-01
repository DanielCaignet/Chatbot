---
tipo: concepto
titulo: "Ledger del turno"
alias: [sas_ledger]
creado: 2026-10-01
actualizado: 2026-10-01
---

# Ledger del turno

## Definicion
Registro, por conversación y turno, de cada resultado que devolvieron las herramientas del SAS. El verificador compara contra él cada número, precio, SKU, fecha u hora de la respuesta antes de enviarla.

## Por que importa en este proyecto
Convierte el 'no inventar' en una compuerta determinista: lo que no está en el ledger no sale. Patrón heredado de la verificación de cifras de CristalChile [INT:D:/Dataseed/CristalChile-Maqueta/src/ui_conversa.py].

## Se relaciona con
[[Capa SAS]] · [[Anclaje]]

## Aparece en
[[ADR-005]]
