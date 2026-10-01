---
tipo: fuente
titulo: "Hermes Agent api_server"
autores: []
anio: 2026
url: "https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server"
archivo_local: ""
creado: 2026-10-01
---

# Hermes Agent api_server

## TL;DR
Documentación del api_server de Hermes Agent (NousResearch, ~250k estrellas) y de su modelo de seguridad (/docs/user-guide/security).

## Que aporta a este proyecto
Contrato de integración del arnés ([[ADR-002]]).

## Datos duros
- Endpoint compatible con OpenAI; sesiones por `X-Hermes-Session-Id`; memoria por `X-Hermes-Session-Key`.
- `gateway.api_server.max_concurrent_runs` = 10 por defecto; al llenarse responde **HTTP 429** [Seguro].
- `GET /v1/toolsets` lista las toolsets activas del api_server.
- Ocho capas de seguridad; aislamiento entre sesiones [Seguro].

## Conceptos
[[Capa SAS]]
