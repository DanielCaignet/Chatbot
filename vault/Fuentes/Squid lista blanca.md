---
tipo: fuente
titulo: "Squid lista blanca"
autores: []
anio: 2026
url: "https://wiki.squid-cache.org/SquidFaq/SquidAcl"
archivo_local: ""
creado: 2026-10-03
---

# Squid lista blanca

## TL;DR
Squid es un proxy HTTP; con ACL (listas de control) se permite solo CONNECT al puerto 443 de dominios concretos y se niega lo demás.

## Que aporta a este proyecto
Contención de red de Hermes en T014: sin ruta a Internet salvo el proxy, y el proxy solo deja pasar al proveedor de modelos ([[Hermes Agent api_server]]).

## Datos duros
- ACL `dstdomain`, `port` y `method CONNECT` con `http_access allow … ; http_access deny all` [Seguro, https://wiki.squid-cache.org/SquidFaq/SquidAcl].
- Imagen `ubuntu/squid:6.6-24.04_edge` (Canonical, incluye arm64) [Seguro, manifiesto comprobado en la VM 2026-10-03].
