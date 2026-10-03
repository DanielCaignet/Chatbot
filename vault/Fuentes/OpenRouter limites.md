---
tipo: fuente
titulo: "OpenRouter limites"
autores: []
anio: 2026
url: "https://openrouter.ai/docs/api-reference/limits"
archivo_local: ""
creado: 2026-10-01
---

# OpenRouter limites

## TL;DR
Límites de crédito y de tasa de OpenRouter.

## Que aporta a este proyecto
Restricción del perfil de desarrollo ([[ADR-004]]).

## Datos duros
- Modelos `:free` con tope por minuto y por día que depende de si se compraron créditos alguna vez [Seguro].
- Crear más cuentas o llaves no sube el límite: se gobierna globalmente [Seguro].
- El tope diario de los `:free` es por cuenta y común a todos ("requests per day total"); las cifras exactas son plantillas sin rellenar en la documentación y se leen en `GET /api/v1/key` (`free_model_daily_requests`) [Seguro, https://openrouter.ai/docs/faq y /api-reference/limits, leídas 2026-10-03]. Medido en la cuenta de Richard el 2026-10-03: 50 por día, sin créditos comprados [Seguro].
- Un 429 puede venir de OpenRouter (tope de plataforma) o del proveedor del modelo; solo el segundo se arregla probando otro modelo, con el parámetro `models` (https://openrouter.ai/docs/guides/routing/model-fallbacks) [Seguro].

## Conceptos
[[ADR-004]]
