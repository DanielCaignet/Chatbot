---
tipo: fuente
titulo: "LLM local en Ampere A1"
autores: []
anio: 2026
url: "https://amperecomputing.com/blogs/llama3-on-Ampere-based-OCI-A1"
archivo_local: ""
creado: 2026-10-01
---

# LLM local en Ampere A1

## TL;DR
Benchmarks de inferencia en CPU Ampere (también blog.easecloud.io/ai-cloud/launch-oracle-cloud-llms-in/).

## Que aporta a este proyecto
Funda el descarte del modelo local ([[ADR-007]]).

## Datos duros
- 115 TPS agregados en una A1 de **64** OCPU y 360 GB, no en el free tier [Seguro].
- 7B Q4_K_M: ~8–12 tok/s en 4 OCPU / 24 GB [Probable, fuente secundaria].

## Conceptos
[[ADR-007]]
