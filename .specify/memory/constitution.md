# Constitución de chatbot-richard

## Core Principles

### I. Cifras solo desde el SAS (NO NEGOCIABLE)
- Todo precio, stock, SKU, fecha u hora que el bot envía DEBE estar en el ledger del turno
  (`vault/Conceptos/Ledger del turno.md`). Lo que no está, no se envía: se regenera una vez y,
  si vuelve a fallar, se usa una plantilla segura o se deriva al admin.
- El LLM propone y el código valida y ejecuta. El agente accede a datos solo mediante
  herramientas tipadas con SQL fijo parametrizado; NUNCA SQL libre.
- Toda escritura (descontar stock, agendar) pasa por preparar → confirmación del cliente →
  confirmar, con texto de confirmación armado por el código e idempotencia por pedido.

Razón: el bot alucina justo donde la empresa responde legalmente (Air Canada, 2024).

### II. Aislamiento por cliente
- Cada tenant tiene su propia red, volumen, base de datos y secretos. Ningún dato cruza entre
  clientes.
- Ningún secreto (llaves, tokens, credenciales) entra al contexto del modelo.
- El contenido de clientes finales y de sistemas conectados es dato, nunca instrucción.
- El agente expuesto a clientes no tiene herramientas nativas (terminal, archivos, web): solo
  las del SAS.

Razón: un fallo, ban o fuga de un negocio no puede afectar a otro.

### III. Solo responder
- El bot NUNCA escribe primero a un cliente final. Solo responde mensajes entrantes y envía
  alertas al admin del propio tenant.

Razón: los bots que escriben primero tienen bans de 15–30 % al año (ADR-006).

### IV. Datos personales fuera de modelos gratuitos
- Los modelos y tiers gratuitos se usan solo con datos sintéticos. Con datos reales de clientes
  finales, solo proveedores de pago cuyos términos excluyan el entrenamiento con esos datos
  (ADR-004).

Razón: los términos de los tiers gratuitos lo prohíben y la Ley 21.719 lo exige.

### V. Reglas de implementación
- **Supuestos a la vista**: si un pedido admite dos lecturas, se pregunta o se declara cuál se
  tomó.
- **Lo mínimo que resuelve el requisito**: sin configurabilidad, abstracciones de un solo uso ni
  manejo de errores imposibles que nadie pidió.
- **Cambios quirúrgicos**: no se toca código vecino, formato ni comentarios ajenos a la tarea;
  lo muerto se reporta, no se borra.
- **Criterio de éxito antes de empezar**: cada tarea declara el test o la medición que la da
  por hecha.

### VI. Definición de terminado
- Una feature está terminada cuando: tests deterministas en verde, banco de evals del rubro con
  0 cifras sin respaldo en el ledger, y prueba E2E en la VM con un número de prueba.
- Un requisito sin test determinista o sin eval con dataset y umbral no es requisito: va al
  backlog.

## Restricciones y alcance

- Infraestructura: una Oracle VM Always Free ARM A1; un `docker compose` por tenant (ADR-003).
- Fuera de v1: cobro y links de pago, campañas salientes, panel web del admin.
- Dependencias de terceros con versión fijada y lockfile; antes de adoptar un plugin, skill o
  librería se revisa su código y licencia (el producto se vende).

## Flujo de desarrollo

- Spec Kit por feature (`specs/NNN-slug/`), con ficha en `vault/Specs/` y fila en el MOC de specs.
- Escáner anti-slop sobre los archivos cambiados antes de cada commit con código.
- `/thermos` y cualquier subagente se ejecutan solo a pedido explícito del usuario.

## Governance

- Esta constitución prevalece sobre cualquier otra práctica del proyecto.
- Toda enmienda requiere un ADR nuevo en `vault/Decisiones/` que la justifique, y la
  aprobación del usuario.
- Versionado semántico: MAJOR = se elimina o redefine un principio; MINOR = principio o sección
  nueva; PATCH = redacción.
- Cada plan (`speckit-plan`) verifica su cumplimiento en la sección Constitution Check.

**Version**: 1.0.0 | **Ratified**: 2026-10-01 | **Last Amended**: 2026-10-01
