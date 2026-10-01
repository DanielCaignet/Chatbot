# full-autodev · Fase 6

> Se carga desde `SKILL.md` al cerrar un hito. Las reglas del núcleo (`SKILL.md`) siguen rigiendo acá.

## Fase 6 — Retroalimentación (la línea de mejora)

Sin esto el andamiaje se congela en las reglas del primer día. Correr al cerrar un hito,
no en cada fase.

```bash
python "$env:USERPROFILE\.claude\skills\full-autodev\references\gates.py" --stats
```

Lee `.gates/history.jsonl` (una línea por corrida, la escribe `gates.py` solo) y
`.gates/feedback.md`. Muestra tres señales:

| Señal | Qué significa | Qué hacer |
|---|---|---|
| **Regla que nunca disparó** | o el proyecto no la necesita, o está mal escrita y no puede disparar | revisarla o retirarla; una regla muerta da falsa sensación de cobertura |
| **Regresión** | más hallazgos que la corrida anterior | atenderlo antes de seguir |
| **Falso positivo** (en `feedback.md`) | la compuerta bloqueó algo correcto | **el más caro**: enseña a usar `--no-verify`, y desde ahí la compuerta dejó de existir |

Resolver una observación es una de dos:

1. **Ajustar `gates.toml`** — queda local al proyecto.
2. **Promover el cambio a `gates.py` + el archivo de la skill que sea dueño de la regla** (`SKILL.md` o su `references/*.md`) y anotarlo en `references/CHANGELOG.md`.
   Esto es lo que hace que el sistema mejore en **todos** los proyectos.

La fuente más valiosa de mejora es un proyecto real que resolvió algo mejor que la plantilla:
**eso se porta hacia la plantilla, nunca al revés.** Ver la entrada v0.2 del CHANGELOG como
ejemplo de cómo se hace.
