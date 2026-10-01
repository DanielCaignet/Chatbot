# full-autodev · Fases 1 a 4

> Se carga desde `SKILL.md` desde la entrevista hasta el plan y las tareas. Las reglas del núcleo (`SKILL.md`) siguen rigiendo acá; el Ciclo de cierre también está ahí.

## Fase 1 — Entrevista informada

Se pregunta **después** de mirar lo que ya existe, no antes.

1. Si el directorio tenía código o documentos previos, extraer primero sin gastar tokens:
   ```bash
   graphify update .        # AST, sin LLM
   ```
   Consultar lo detectado con `graphify query` y abrir la entrevista por lo que **falta**, no con un cuestionario genérico.

2. Preguntar con `AskUserQuestion`, máximo 4 por tanda, en este orden:
   - **Dominio y alcance** — qué problema resuelve, qué queda explícitamente fuera.
   - **Invariantes** — qué no puede romperse nunca (van a la constitución).
   - **Stack y restricciones** — lenguaje, despliegue, dependencias impuestas.
   - **Definición de terminado** — cómo se verifica que una feature está lista.
   - **Fuentes externas** — papers, docs de vendor, APIs que hay que fichar.

3. **Cada respuesta se escribe en su ficha dueña en el momento.** Un término nuevo → `vault/Conceptos/<X>.md`. Una decisión → `vault/Decisiones/ADR-NNN`. Una restricción dura → candidata a constitución. El hilo de chat se pierde; las fichas no.

4. Cerrar construyendo el grafo por primera vez: seguir la skill `graphify` sobre la raíz. Después, **Ciclo de cierre**.

---

## Fase 2 — Constitución

1. Consultar: `graphify query "invariantes restricciones del proyecto"`.
2. Invocar la skill `speckit-constitution` con la herramienta Skill. Spec Kit instala sus comandos como **skills** en `.claude/skills/speckit-*`, no como comandos `/speckit.*`. Si los nombres no coinciden, listarlos: `ls .claude/skills/` o `specify artifact list`.
3. La constitución lleva **solo invariantes**: reglas que no cambian por feature. Nada de estado, nada de roadmap, nada de "actualmente estamos en X" — eso vive en `STATE.md`.
   Si el usuario no fija otras, propone estas cuatro reglas de implementación como invariantes
   por defecto (idea de las guías de Karpathy, ver `calidad.md`). Se proponen y el usuario las
   aprueba, no se imponen:
   - **Supuestos a la vista antes de codear.** Si el pedido admite dos lecturas, se pregunta o se
     declara cuál se tomó. No se elige en silencio.
   - **Lo mínimo que resuelve el requisito.** Nada de configurabilidad, abstracciones de un solo
     uso ni manejo de errores imposibles que nadie pidió.
   - **Cambios quirúrgicos.** No se mejora código vecino, formato ni comentarios que no hacen
     falta para la tarea. Lo muerto que se vea se reporta, no se borra.
   - **Criterio de éxito antes de empezar.** Cada tarea declara qué test o qué medición la da
     por hecha, y se itera hasta cumplirlo. Es la forma operativa de la Regla de admisión de
     requisitos.
4. Registrar `vault/Decisiones/ADR-000-constitucion.md` enlazando los `[[Conceptos]]` involucrados.
5. Ciclo de cierre.

---

## Fase 3 — Spec

Acá se previene "olvidé un spec". **En este orden, sin saltear:**

1. Leer `vault/MOCs/00 - Indice de Specs.md`. Es el registro completo, es chico, es barato.
2. `graphify query "<lo que se va a especificar>"` — ¿ya hay un nodo que lo cubre?
3. `graphify affected "<concepto central>"` — ¿qué specs existentes quedan afectados o superados?

Resolución:
- Si ya existe un spec que lo cubre → **no crear uno nuevo.** Extenderlo, o marcar el viejo `superseded` y poner `supersedes:` en el nuevo. Decirlo explícitamente.
- Si no existe → continuar.

Luego:

4. Skill `speckit-specify` con la descripción → Spec Kit crea `specs/NNN-slug/spec.md`.
5. Si hay ambigüedad, skill `speckit-clarify` antes de planificar.
6. **Crear la ficha de registro** desde `vault/Specs/_TEMPLATE-SPEC.md`. La ficha no repite el spec: lleva frontmatter (`id`, `status: vigente`, `spec_path`, `supersedes`) y wikilinks a los `[[Conceptos]]` y `[[ADR-NNN]]` que toca. Es lo que hace al spec encontrable en el grafo.
   - `status` no mide avance: solo dice si el spec rige (`vigente`) o fue reemplazado (`superseded`).
   - La ficha **no lleva nivel de madurez**: su dueño único es la fila del MOC.
7. Agregar la fila en `vault/MOCs/00 - Indice de Specs.md` con `Nivel = N0` (contrato escrito, nada implementado). **Omitir este paso es la falla `SPEC-UNINDEXED`.**

> Corregido 2026-09-23: el frontmatter usaba `status` como avance binario (`draft|active|done`), que v0.2 reemplazó por niveles de madurez. Ver CHANGELOG v0.2.1.
> Corregido 2026-09-23 (v0.2.2): la corrección anterior ponía `nivel:` en la ficha **y** en el MOC, dos dueños del mismo hecho. El nivel queda solo en el MOC, que es lo que lee `G-N1`.
8. Ciclo de cierre.

---

## Fase 4 — Plan y tareas

1. Consultar antes de diseñar: `graphify query "<módulos que toca>"` y `graphify affected "<módulo>"`. El plan cita rutas y nodos reales, no suposiciones.
2. Skills `speckit-plan` → `speckit-tasks` → `speckit-analyze` (y `speckit-checklist` si la feature lo amerita).
3. **Chequeo que `speckit-analyze` no hace:** por cada artefacto nuevo que el plan proponga crear, `graphify query` sobre su nombre. Si ya existe un nodo equivalente, reusar y anotarlo en el plan.
4. Toda decisión de diseño no obvia → `vault/Decisiones/ADR-NNN`. El plan la enlaza, no la reargumenta.
5. Ciclo de cierre.
