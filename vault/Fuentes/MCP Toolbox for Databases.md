---
tipo: fuente
titulo: "MCP Toolbox for Databases"
autores: []
anio: 2026
url: "https://github.com/googleapis/genai-toolbox"
archivo_local: ""
creado: 2026-10-01
---

# MCP Toolbox for Databases

## TL;DR
Servidor MCP de Google para bases de datos; herramientas declaradas en tools.yaml.

## Que aporta a este proyecto
Candidato para servir las herramientas de lectura del SAS ([[ADR-005]]).

## Datos duros
- Herramientas custom con `statement` SQL fijo y `parameters` tipados [Seguro].
- Prebuilts por motor (`--prebuilt=postgres`) incluyen SQL libre: **no usar**.
- Soporta Postgres, MySQL, SQLite y otros.

## Conceptos
[[Capa SAS]] · [[Catalogo semantico]]
