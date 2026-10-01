---
tipo: concepto
titulo: "Catalogo semantico"
alias: [semantic.yaml]
creado: 2026-10-01
actualizado: 2026-10-01
---

# Catalogo semantico

## Definicion
Descripción congelada de los datos de un cliente: entidades, grano, clave y campos tipados (id, cat, texto, numero, dinero, stock, fecha). Se genera por introspección del esquema, el LLM puede proponer etiquetas y el admin la aprueba.

## Por que importa en este proyecto
Es lo que hace genérico al producto: de él salen las herramientas tipadas (tools.yaml de MCP Toolbox) para cualquier BD del cliente o plantilla de rubro.

## Se relaciona con
[[Capa SAS]] · [[Rubro]]

## Aparece en
[[ADR-005]]
