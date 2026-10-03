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
- Toolsets núcleo (nombres para `disabled_toolsets`): browser, clarify, code_execution, computer_use, connections, cronjob, delegation, desktop_ui, discord, discord_admin, feishu_doc, feishu_drive, file, homeassistant, image_gen, kanban, memory, project, search, session_search, setup, skills, spotify, terminal, todo, tts, video, video_gen, vision, web, x_search, yuanbao. Las compuestas (coding, debugging, safe) se arman con ellas [Seguro, https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference, leída 2026-10-03].
- El tope `max_concurrent_runs` cubre los endpoints compatibles con OpenAI, `/v1/runs` y los de sesión; responde 429 `Too many concurrent runs (max N)` [Seguro, doc del api_server, leída 2026-10-03].
- `GET /v1/toolsets` devuelve `{"object":"list","platform":"api_server","data":[{name, label, enabled, configured, tools[]}]}` (la documentación muestra una lista simple; medido en v2026.9.24: 29 toolsets, solo nativas, sin las herramientas de la MCP, que sí quedan registradas como `mcp__<servidor>__<herramienta>`) [Seguro, medido 2026-10-03]; `X-Hermes-Session-Id` en Chat Completions continúa la sesión con su historial del servidor [Seguro, misma doc].
- Docker: imagen `nousresearch/hermes-agent` (etiqueta de versión `v2026.9.24`, amd64 y arm64), datos en `/opt/data`, `gateway run`; el arranque siembra `config.yaml` si falta; MCP por `mcp_servers.<nombre>.url` con `tools.include` [Seguro, https://hermes-agent.nousresearch.com/docs/user-guide/docker y /features/mcp, leídas 2026-10-03].
- `${VAR}` se expande en `config.yaml`; una variable no definida queda literal y solo avisa en el registro, así que un `OPENROUTER_MODEL` vacío no falla al arrancar [Seguro, https://hermes-agent.nousresearch.com/docs/user-guide/configuration, leída 2026-10-03].
- Medido en v2026.9.24 (2026-10-03): Hermes añade las herramientas internas `tool_search` y `tool_describe` para descubrir las de la MCP, y no figuran en `/v1/toolsets`; el log de herramientas está en `/opt/data/logs/agent.log` con el formato `[<sesión>] agent.tool_executor: tool <nombre> completed`; cuando el proveedor limita, Hermes responde HTTP 200 con un texto que dice "rate-limited", no un 429; cada sesión nueva gastaba una llamada extra para el título (`auxiliary.title_generation.enabled: false` la apaga); el prompt propio de Hermes pesa ~2.300 tokens por turno [Seguro, medido].
- Sin confirmar: que el cliente de modelos de Hermes respete `HTTPS_PROXY`; lo mide T014 [Adivinando].

## Conceptos
[[Capa SAS]]
