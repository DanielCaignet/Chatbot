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
- Formato actual de `tools.yaml` (documentos separados por `---`): `kind: source` con `type: postgres`, y `kind: tool` con `type: postgres-sql`, `source`, `description`, `parameters` (name, type, description) y `statement` con `$1`, `$2`… Las versiones viejas usaban un mapa `tools:` con `kind:` por herramienta; hay que fijar la versión del binario [Seguro, https://mcp-toolbox.dev/documentation/configuration/tools/ y /configuration/, leídas 2026-10-03].
- Tipos de parámetro: `string`, `integer`, `float`, `boolean`, `array`. `allowedValues` (acepta regex) restringe la entrada; los *template parameters* insertan texto en el SQL y son propensos a inyección: no usarlos [Seguro].
- Contraseñas y usuarios por variable de entorno con `${NOMBRE}` (valor por defecto: `${NOMBRE:valor}`) [Seguro].
- El servidor MCP está en `http://127.0.0.1:5000/mcp` (transporte HTTP) [Probable, ejemplo de cliente en la documentación oficial].
- El origen (`kind: source`, `type: postgres`) lleva su propio usuario y contraseña: la solo-lectura se logra dándole un rol de BD sin permisos de escritura, no con una opción del Toolbox [Probable].

## Conceptos
[[Capa SAS]] · [[Catalogo semantico]]
