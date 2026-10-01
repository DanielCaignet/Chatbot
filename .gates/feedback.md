# Retroalimentacion de compuertas — chatbot-richard

Linea de mejora del andamiaje. `gates.py --stats` lee este archivo y muestra lo pendiente.
Sin esto, el linter se congela en las reglas del primer dia.

Se registran **tres cosas y nada mas**:

1. **Falso positivo** — la compuerta bloqueo algo correcto. Es el mas caro: ensena a saltarse
   el linter con `--no-verify`, y desde ahi la compuerta ya no existe.
2. **Falla no atrapada** — algo se rompio y ninguna compuerta lo vio. Es una regla que falta.
3. **Regla muerta** — `--stats` la muestra sin disparar nunca. O el proyecto no la necesita,
   o esta mal escrita y no puede disparar.

Resolver una observacion es una de dos: ajustar `gates.toml` (local a este proyecto), o
**promover el cambio a la plantilla** en `~\.claude\skills\full-autodev\references\gates.py`
y anotarlo en su `CHANGELOG.md`. Lo segundo mejora todos los proyectos, no solo este.

Correccion con la cicatriz a la vista: una observacion resuelta no se borra, se marca `- [x]`
con la fecha y que cambio.

---

## Pendientes

_ninguna todavia_

## Resueltas

_ninguna todavia_