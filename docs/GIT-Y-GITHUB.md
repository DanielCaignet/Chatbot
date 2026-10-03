# Git y GitHub: buenas prácticas automáticas (pedido por Richard, 2026-10-02)

> Dueño único del ciclo de Git del proyecto. `CLAUDE.md` solo resume lo esencial y enlaza aquí.
> El agente lo lee antes del primer commit de cada sesión y lo ejecuta solo, sin que se lo pidan.

Richard no domina Git (herramienta que guarda versiones del proyecto). **El agente ejecuta este
ciclo solo, cada vez que corresponda, sin que Richard lo pida**. En el chat solo informa el
resultado (qué se guardó y dónde está el PR), según las reglas de comunicación de `CLAUDE.md`. Repositorio: `origin` = `DanielCaignet/Chatbot` (público); Richard entra
como `richardcaignetlorenzo-crypto` con permiso de escritura (verificado 2026-10-02, `push: true`).

## Cuándo corresponde
- **Commit (guardar una versión):** al terminar una unidad con sentido: un spec, un plan, un
  grupo de fichas del vault, un cambio de reglas. No al final de la sesión en un bloque gigante.
- **Push + pull request:** al cerrar el conjunto de commits de una rama (por ejemplo un spec
  completo en su etapa) o cuando Richard lo pida.

## Pasos, en orden
1. **Rama (copia paralela para no tocar `main`).** Nunca se trabaja directo en `main`. Una rama por
   spec, con el mismo nombre que su carpeta: `NNN-slug` (ej. `001-spike-viabilidad`). Para cambios
   sin spec: `docs/<tema>`, `fix/<tema>` o `chore/<tema>`. Se crea desde `main` actualizado.
2. **Revisar antes de guardar.** `git status` (qué archivos cambiaron) y `git diff` (qué cambió
   dentro). Agregar archivos **por nombre**, nunca `git add .` ni `-A`. Confirmar que no entra
   ninguna llave, token, `.env` ni dato real (Constitución II y IV). Lo que no pertenece al cambio
   queda fuera.
3. **Commits pequeños y atómicos (una sola idea cada uno).** Si el trabajo pendiente mezcla
   varias ideas, se parte en varios commits.
4. **Mensaje en formato Conventional Commits (etiqueta al inicio):** `tipo(ámbito): resumen en
   imperativo, ≤72 caracteres`. Tipos: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
   Cuerpo opcional: el **porqué**, no el qué. Termina con la línea de coautoría que indique el
   sistema. Ejemplo: `docs(spec-001): plan del spike de viabilidad F1`.
5. **El pre-commit (revisión automática que corre al guardar) no se salta jamás.** Nada de
   `--no-verify`. Si falla (escáner `SLOP-SCAN`, gates), se corrige la causa y se hace un commit
   **nuevo**; no se usa `--amend` (reescribir el último commit) salvo que Richard lo pida.
6. **Antes de subir:** traer cambios (`git fetch`) y comprobar que la rama no quedó atrás de `main`;
   si quedó, usar `sync_with_base_branch` si hay worktree, o `git merge origin/main`, y resolver
   conflictos.
7. **Push (enviar la rama a GitHub):** `git push -u origin <rama>`. **Nunca** `--force` (sobrescribir
   el historial) ni push a `main`.
8. **Pull request (propuesta de unir la rama a `main`) con `gh pr create`:**
   - Título corto con el mismo formato de commit.
   - Cuerpo con: **Qué cambia** · **Por qué** · **Cómo se comprobó** · **Qué falta o queda
     bloqueado** · enlaces al spec/ADR. Termina con la línea de atribución que indique el sistema.
   - Si el PR es borrador (trabajo incompleto), abrirlo con `--draft`.
9. **Después de abrirlo:** llamar `get_status` de las herramientas `ccd_pr`; si no reporta ese PR,
   `bind_pr`. Leer el estado de las comprobaciones (CI: revisión automática en GitHub) y ofrecer
   a Richard el auto-fix si fallan. **No** programar ni consultar CI en bucle por cuenta propia.
10. **Unir (merge) solo con aprobación explícita de Richard**, nunca con auto-merge salvo que lo
    pida. Antes de unir, **preguntar** si quiere `/thermos` (regla del stack de calidad). Tras
    unir: volver a `main`, actualizarlo y borrar la rama local.
11. **Al cerrar una fase:** `graphify update .` y `graphify save-result` (ver "Al cerrar cada
    fase"); se commitean aparte con `chore(graphify): …` si cambiaron archivos versionados.

## Prohibido sin permiso explícito de Richard
- `git push --force`, `git reset --hard`, `git checkout -- <archivo>`, `git clean -f`, borrar
  ramas remotas, reescribir historial publicado.
- Saltarse hooks (`--no-verify`) o firmas.
- Commitear secretos, `.env`, llaves, credenciales o datos personales reales.
- Unir PRs, cambiar la configuración del repositorio o de GitHub, cerrar o comentar issues ajenos.
- Subir a un repositorio que no sea `DanielCaignet/Chatbot` (si algún día se usa un *fork*, copia
  propia del repositorio, se pide confirmación una vez y se anota aquí).
