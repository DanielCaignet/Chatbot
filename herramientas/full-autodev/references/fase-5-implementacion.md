# full-autodev · Fase 5

> Se carga desde `SKILL.md` al escribir código de una feature. Las reglas del núcleo (`SKILL.md`) siguen rigiendo acá; el Ciclo de cierre también está ahí.

## Fase 5 — Implementación

1. Skill `speckit-implement` (y `speckit-converge` al cerrar la feature).
   **Anti-slop va en cada modificación de código, no sólo al cerrar la feature:** la skill
   `anti-slop` aplica mientras se escribe, y antes del commit de ese cambio corre el scanner sobre
   los archivos cambiados. Un `high` que introduce el cambio se corrige antes del commit; uno que
   ya estaba se reporta al usuario. Recién después, `--sellar` y commit. Un cambio que no pasó por
   el scanner no se commitea, aunque sea un refactor que «no cambia nada».
2. El hook post-commit reconstruye el grafo solo. Si se trabajó sin commitear: `graphify update .`
3. Antes de subir el nivel, en este orden:
   1. Si la feature toca UI: abrirla corriendo en el navegador del host (el integrado, o Claude in Chrome si el usuario lo pide) y recorrer el flujo del requisito. Un test verde no muestra un botón tapado ni un estado vacío roto. Lo visto va como `[MEDIDO]` con fecha. Sin navegador disponible, decirlo; no se da por verificado.
   2. `gates.py`: ninguna afirmación `[INT?]` sobrevive al cierre (`G-REF`), todo requisito tiene verificación (`G-EARS`, `G-VERIF`) y `SLOP-SCAN` no deja nada `high`.
   3. `/slop-check diff`: revisión semántica del diff de la feature.
   4. Para subir a `N2`/`N3` o antes de fusionar el PR: `/thermos` y `/slop-check pr` sobre la rama. Un hallazgo bloqueante se corrige antes de subir. Uno no bloqueante va a una tarea o a una decisión, no se queda en el chat.
4. Subir `Nivel` en la fila del MOC al alcanzado de verdad, con su `Limite`. Es el único lugar donde vive el nivel.
   - `N1` exige en `Limite` una frase refutable de al menos 6 palabras (`G-N1`, bloquea el commit). Sin ella, el nivel sigue en `N0`.
   - `N2`/`N3` solo con producción real, citando el caso en `Limite` (`[INT:<ruta>]` o `[MEDIDO]`).
   - No existe "terminado": la feature queda **cerrada en un nivel**, y así se muestra.
   - Si la ficha y el MOC discrepan en `status`, es `INDEX-DRIFT`.
5. Ciclo de cierre.

> Corregido 2026-09-23: el paso 3 cerraba la ficha con `status: done`, reintroduciendo el estado binario que v0.2 eliminó. Ver CHANGELOG v0.2.1.
> Corregido 2026-09-23 (v0.2.2): el nivel se actualizaba en la ficha y en el MOC; ahora solo en el MOC.

## Depuración: causa raíz antes del parche

Ante un bug, un test que falla o un hallazgo de review. Adoptado el 2026-09-29 a partir de
la idea de `systematic-debugging` de Superpowers (ver `calidad.md`, candidatos evaluados). Se
escribió aquí con las reglas de esta skill; el texto original no se copió.

1. **Reproducir.** Un comando o un test que falla de forma determinista. Sin reproducción no hay
   diagnóstico, sólo una conjetura: se dice así y se pide el dato que falta.
2. **Acotar con el grafo.** `graphify query "<síntoma>"` y `graphify affected "<símbolo>"` para ver
   por dónde pasa el flujo y qué más lo usa. Leer sólo los `source_location` que aparecen.
3. **Una hipótesis a la vez**, escrita antes de tocar código: «falla porque X; si es así, Y
   debería verse». Se comprueba Y midiendo. Si no se ve, la hipótesis se descarta y se anota.
4. **El arreglo va con su test.** Primero el test que reproduce el bug y falla, después el
   cambio mínimo que lo pone verde. Sin tocar código vecino que no está roto.
5. **Tres intentos fallidos significan que el modelo mental está mal**, no que falta un cuarto
   parche. Parar, volver al paso 2 con `drilling-design-problems`, y decirlo al usuario.

La causa raíz y lo descartado van a un ADR cuando cambian una decisión, o al commit cuando no.
En el chat se pierden.
