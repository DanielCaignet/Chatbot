# Backlog del stack de full-autodev

Pendientes del stack (herramientas, modelos, compuertas), no de un proyecto. Lo que se resuelve pasa a `CHANGELOG.md`.

## Que el hook verifique el modelo del revisor de bugs en PRs que llegan a `N2`+

- **Abierto:** 2026-09-24. La regla del modelo por etapa quedó escrita el 2026-09-26 (`~/.claude/CLAUDE.md`, «Costo de thermos»; `CHANGELOG.md` v0.4.2). Falta la compuerta.
- **Hoy:** `--sellar-thermos` no registra qué modelo corrió cada revisor. Un PR que sube un spec a `N2` puede sellarse con el revisor de bugs en Sonnet, y nada lo avisa.
- **Por qué importa:** subir a `N2` es la compuerta que exige thermos. Si el revisor de bugs en Sonnet es el que la habilita, el ahorro de la etapa temprana termina aprobando el paso a producción.
- **Falta definir:** cómo lee el hook el nivel. Hoy el MOC es markdown propio de cada proyecto; habría que exponerlo desde `gates.py` o desde `gates.toml`.
- **Hecho cuando:** el sello registra el modelo del revisor de bugs, y un merge que deja un spec en `N2`+ sellado con Sonnet queda bloqueado o avisado.

## Evaluar si la calidad de los revisores en Sonnet alcanza

- **Abierto:** 2026-09-26.
- **Qué mirar:** en las síntesis de thermos, los casos en que el revisor en Sonnet pasó por alto algo que después encontró el de Opus, otra ronda o el uso real. Sin esos datos, la regla de modelo por etapa es una apuesta de costo.
- **Hecho cuando:** hay al menos 5 PRs comparables y una decisión escrita en `CHANGELOG.md`: se mantiene la regla, o se vuelve a usar Opus en alguna etapa.
