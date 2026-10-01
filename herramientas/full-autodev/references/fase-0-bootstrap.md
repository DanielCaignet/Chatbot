# full-autodev · Fase 0

> Se carga desde `SKILL.md` al montar un proyecto nuevo. Las reglas del núcleo (`SKILL.md`) siguen rigiendo acá; el Ciclo de cierre también está ahí.

## Fase 0 — Bootstrap

**Spec Kit es opcional, y lo primero es averiguar si estorba.** Si el proyecto ya tiene una
convención de specs viva —plantilla propia, numeración propia, compuertas propias— imponerle
`specs/NNN-slug/` es duplicación estructural, no una mejora. En ese caso: `-NoSpecKit`, se
conserva su convención, y la plantilla aporta solo lo que falta (grafo, orientación, compuertas).

> Corregido 2026-09-23 (v0.4): «convención viva» significa **una spec por feature**. Una sola
> spec paraguas para todo el proyecto no es una convención que resuelva mejor: se monta Spec Kit,
> la paraguas se conserva para lo transversal (parámetros, datos) y las features se descomponen
> **desde lo que el cliente pidió por escrito**, no desde el código. Así se hizo en CristalChile
> (SPEC-001 → specs 002–010). Lo que sí se conserva siempre son las compuertas propias del
> proyecto: los requisitos de las specs nuevas apuntan a ellas como método de verificación.

Lo mismo vale para el resto: **si el proyecto resuelve algo mejor que esta plantilla, se porta
hacia la plantilla** (Fase 6 y `references/CHANGELOG.md`), no se le impone la versión peor.

Un comando, idempotente. Escanea primero y decide por pieza: `fresh` (crear), `incremental` (completar lo que falta), `skip` (ya está). Nunca pisa contenido escrito por una persona.

```powershell
& "$env:USERPROFILE\.claude\skills\full-autodev\references\bootstrap.ps1" -Path "<ruta>" -Name "<nombre>" -Profile software
```

Perfiles: `software` (agrega `vault/Componentes/`), `research` (`Metodos/`, `Resultados/`), `data` (`Datasets/`, `Experimentos/`). El resto de la estructura es común.

Deja montado:

```
<raíz>/
├─ STATE.md                  ← archivo 1 de 2 de orientación (se sobreescribe)
├─ CLAUDE.md                 ← manual operativo + sección graphify
├─ .mcp.json                 ← conector graphify-mcp del proyecto
├─ .obsidian/app.json        ← la raíz ES el vault, no una copia
├─ .specify/                 ← specify init --here --integration claude
├─ specs/                    ← features de Spec Kit
└─ vault/
   ├─ AGENT-INDEX.md         ← archivo 2 de 2 de orientación
   ├─ MOCs/                  ← 00 Specs · 01 Conceptos · 02 Decisiones · 03 Fuentes
   ├─ Specs/ Conceptos/ Decisiones/ Fuentes/   ← con _TEMPLATE-*.md
   └─ <extras del perfil>
```

Más: `graphify claude install` (sección en CLAUDE.md + hook PreToolUse), `graphify hook install` (post-commit/post-checkout que reconstruye el grafo solo), y `graphify-out/` en `.gitignore`.

Reportar en una línea qué creó y qué ya existía. Si `specify init` falla, seguir con el resto y decirlo: el vault y el grafo funcionan sin Spec Kit.

**No construir el grafo todavía.** Un proyecto recién montado no tiene nada que extraer.
