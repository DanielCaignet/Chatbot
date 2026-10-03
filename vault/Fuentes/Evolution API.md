---
tipo: fuente
titulo: "Evolution API"
autores: []
anio: 2026
url: "https://github.com/EvolutionAPI/evolution-api"
archivo_local: ""
creado: 2026-10-01
---

# Evolution API

## TL;DR
API de mensajería open source basada en Baileys, con soporte de WhatsApp Cloud API, multi-instancia e integración con Chatwoot.

## Que aporta a este proyecto
Capa de canal adoptada ([[ADR-001]]).

## Datos duros
- Licencia Apache-2.0 con condiciones: no quitar logo/copyright del frontend y **aviso visible** de que se usa Evolution API; si no, licencia comercial [Seguro, LICENSE].
- Multi-instancia: varios números aislados en un despliegue [Probable].
- El webhook `MESSAGES_UPSERT` trae `fromMe`. Hay reportes de recibir `fromMe: true` incluso de mensajes enviados por la propia API (https://github.com/EvolutionAPI/evolution-api/issues/956), así que distinguir humano vs API exige cruzar el id del mensaje con la respuesta del envío [Probable].
- No hay cifras publicadas de RAM por instancia en ARM: se mide en el spike [Seguro que no hay dato].

## Conceptos
[[Canal]] · [[Takeover]]
