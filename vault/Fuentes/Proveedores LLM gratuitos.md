---
tipo: fuente
titulo: "Proveedores LLM gratuitos"
autores: []
anio: 2026
url: "https://openrouter.ai/blog/tutorials/free-llm-apis-compared/"
archivo_local: ""
creado: 2026-10-03
---

# Proveedores LLM gratuitos

## TL;DR
Qué proveedores dan acceso gratuito a un modelo con herramientas y qué cuota propia tiene cada uno, para encadenar respaldos ([[ADR-011]]).

## Que aporta a este proyecto
El tope de 50 solicitudes por día de OpenRouter es común a todos sus `:free` ([[OpenRouter limites]]); otros proveedores tienen cuota propia.

## Datos duros
- Comparativa de terceros, con datos de abril de 2026 y actualizada el 2026-09-24: OpenRouter 20 por minuto y 50 por día (1.000 con 10 USD de recarga); Groq 30 por minuto y ~1.000 por día; Google AI Studio 5–15 por minuto y 20–1.500 por día según modelo; GitHub Models 15 por minuto y 150–1.000 por día; Mistral ~1.000 millones de tokens al mes [Probable, https://openrouter.ai/blog/tutorials/free-llm-apis-compared/, leída 2026-10-03]. **Esa fuente falló en Cerebras**, así que ninguna cifra vale sin confirmarla en el panel de cada cuenta.
- **Cerebras no es gratis permanente:** exige un método de pago verificado; da 5 USD de crédito que caducan a los 30 días, y sin método de pago la API queda inactiva [Seguro, https://inference-docs.cerebras.ai/support/rate-limits, leída 2026-10-03].
- **Google Gemini:** hay nivel gratuito, pero cambia con frecuencia (reportes de Gemini Flash bajando de 250 a 20 solicitudes por día); en el nivel gratuito los datos se usan para mejorar los productos de Google [Probable, https://ai.google.dev/gemini-api/docs/pricing y foros de Google AI, leídos 2026-10-03].
- **Mistral (modo gratuito):** sin tarjeta; los datos pueden usarse para entrenar salvo que se desmarque "Enable data sharing"; los límites exactos se ven en el panel de Mistral Studio [Probable, https://help.mistral.ai y https://docs.mistral.ai/admin/user-management-finops/tier, leídas 2026-10-03].
- **NVIDIA NIM (build.nvidia.com):** 1.000 créditos al registrarse (hasta 5.000 con solicitud), 40 por minuto; son créditos finitos, no una cuota diaria, y NVIDIA no sube el límite a cuentas personales [Probable, foros de NVIDIA, leídos 2026-10-03].
- **GitHub Models:** límites por nivel de modelo, de memoria 10–15 por minuto y 50–150 por día, entrada corta (~8.000 tokens); necesita un token de GitHub con permiso `models:read` [Probable, https://github.com/orgs/community/discussions/143855, leída 2026-10-03].
- **Cloudflare Workers AI:** 10.000 neuronas gratis por día, reinicio a las 00:00 UTC [Seguro, https://developers.cloudflare.com/workers-ai/platform/pricing/].
- Groq y Mistral en Hermes: sus variables `GROQ_API_KEY` y `MISTRAL_API_KEY` son de voz (STT/TTS); para chat se declaran como proveedor personalizado con `providers.<nombre>.api` y `key_env` [Seguro, https://hermes-agent.nousresearch.com/docs/integrations/providers, leída 2026-10-03]. Gemini (`GOOGLE_API_KEY`) y NVIDIA (`NVIDIA_API_KEY`) son proveedores nativos.

## Conceptos
[[ADR-004]]
