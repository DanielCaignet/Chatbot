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
- Las toolsets se apagan con `agent.disabled_toolsets` en `config.yaml`; se aplica después de la config por plataforma, así que gana siempre [Seguro, https://hermes-agent.nousresearch.com/docs/user-guide/configuration].
- **Bug abierto**: con `gateway.multiplex_profiles: true`, el api_server ignora `disabled_toolsets` y las reactiva en silencio (issue #91415, https://github.com/NousResearch/hermes-agent/issues/91415). Este proyecto usa un contenedor por cliente, sin multiplex, pero el spike debe comprobarlo [Seguro que existe el reporte; Adivinando si nos afecta].
- Advertencia oficial: el api_server da acceso completo a las herramientas, **incluido terminal**; `API_SERVER_KEY` es obligatoria en todo despliegue y por defecto escucha solo en `127.0.0.1:8642` (`API_SERVER_ENABLED`, `API_SERVER_PORT`, `API_SERVER_HOST`) [Seguro].

## Conceptos
[[Capa SAS]]
