# Feature Specification: Spike de viabilidad F1 (gate)

**Feature Branch**: `001-spike-viabilidad`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Spike de viabilidad F1 del chatbot multi-cliente para WhatsApp, en la Oracle VM Always Free, con OpenRouter :free y solo datos sintéticos. Cinco verificaciones con criterio pasa/falla y evidencia en el vault: (a) canal, (b) arnés, (c) herramientas de lectura, (d) RAM por stack y cupo de clientes, (e) prueba de descarte de Antigravity. Salida: go/no-go por pieza."

> **Naturaleza del spec.** Es un spike: el producto entregado es un **veredicto con evidencia**,
> no una funcionalidad. Por eso los componentes (canal, arnés, herramientas) se nombran: son el
> objeto medido, no un detalle de implementación. Fuentes del plan: `docs/PLAN-MAESTRO.md` (F1),
> [[ADR-001]], [[ADR-002]], [[ADR-004]], [[ADR-005]], [[ADR-008]].

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Veredicto del arnés de agente (Priority: P1)

Richard necesita saber si Hermes, expuesto por su `api_server` y con **todas las herramientas
nativas apagadas**, puede atender clientes finales no confiables solo con las herramientas del SAS,
a un costo en tokens razonable. Si no, el plan B es un bucle propio ([[ADR-002]]).

**Why this priority**: es la pieza con más riesgo oculto. Hermes nació como agente personal con
terminal y archivos; si no se puede amputar, viola la Constitución II. Además su overhead de prompt
define el costo real por llamada ([[ADR-004]]) y de él depende todo el modelo de negocio.

**Independent Test**: levantar el arnés con el MCP de prueba, correr el banco sintético mínimo y
leer la tabla de resultados; no requiere que exista WhatsApp.

**Acceptance Scenarios**:

1. **Dado** el arnés configurado solo con el MCP del SAS, **Cuando** se lista sus herramientas
   activas, **Entonces** no aparece ninguna nativa (terminal, archivos, web) y un mensaje hostil que
   pide ejecutar un comando o leer un archivo no ejecuta nada.
2. **Dado** 3 conversaciones paralelas con identificadores de sesión distintos, **Cuando** en la
   conversación A se dice un dato inventado y en B se pregunta por él, **Entonces** B no lo conoce.
3. **Dado** más conversaciones simultáneas que el límite de ejecuciones concurrentes (10 por
   defecto), **Cuando** se satura, **Entonces** el arnés responde 429 y, con reintento con espera
   creciente, todas terminan sin pérdida ni duplicado.
4. **Dado** el mismo banco de ≥20 consultas, el mismo modelo y las mismas herramientas, **Cuando** se
   mide Hermes y un bucle de referencia mínimo, **Entonces** se reporta tokens de entrada/salida por
   llamada y su razón; pasa si es ≤ 2×.

---

### User Story 2 - Veredicto del canal WhatsApp (Priority: P1)

Richard necesita saber si Evolution API sobre Baileys sostiene un número real de prueba: conectar,
recibir, responder, **reconectar solo** y distinguir lo que escribe un humano desde el teléfono de lo
que envía el sistema (base del takeover).

**Why this priority**: sin canal estable no hay producto; y el riesgo de ban/inestabilidad de Baileys
es la apuesta más frágil aceptada por el usuario ([[ADR-001]]).

**Independent Test**: vincular el número de prueba y ejecutar el guion de conexión/caída/mensajes;
no requiere el arnés.

**Acceptance Scenarios**:

1. **Dado** un número de prueba vinculado, **Cuando** otro teléfono del equipo le escribe, **Entonces**
   el mensaje llega al receptor del sistema con su contenido y remitente, y una respuesta enviada por
   la API llega al teléfono.
2. **Dado** la instancia conectada, **Cuando** se corta forzosamente el proceso y luego la red,
   **Entonces** vuelve a conectarse sin repetir el emparejamiento y dentro del plazo fijado; se
   registra qué pasó con los mensajes llegados durante la caída.
3. **Dado** un mensaje escrito por una persona desde el propio teléfono y otro enviado por la API,
   **Cuando** ambos llegan al receptor, **Entonces** se pueden distinguir entre sí.

---

### User Story 3 - Herramientas de lectura con SQL fijo (Priority: P2)

Richard necesita saber si MCP Toolbox, con un archivo de herramientas **generado** desde una
descripción del esquema, ofrece lectura segura (SQL fijo, parámetros tipados, solo lectura) o si hay
que escribir un MCP propio ([[ADR-005]]).

**Why this priority**: sostiene la Constitución I (nunca SQL libre). Es P2 porque el arnés puede
probarse con un MCP de prueba mínimo mientras tanto, pero su veredicto decide cómo se construye F2.

**Independent Test**: generar las herramientas del esquema sintético de tienda y atacarlas con
entradas hostiles, sin arnés ni WhatsApp.

**Acceptance Scenarios**:

1. **Dado** un esquema sintético de tienda, **Cuando** se genera la definición de herramientas
   (`catalogo_buscar`, `item_obtener`, `disponibilidad`), **Entonces** cada una ejecuta una consulta
   fija y solo acepta parámetros tipados.
2. **Dado** parámetros con intento de inyección, **Cuando** se invocan, **Entonces** la consulta no
   cambia ni devuelve datos fuera de lo declarado.
3. **Dado** la configuración final, **Cuando** se busca una herramienta de SQL libre, **Entonces** no
   existe ni es invocable; y un intento de escritura con el rol de lectura falla.

---

### User Story 4 - Cupo de clientes por VM (Priority: P2)

Richard necesita saber cuántos clientes caben en la VM, calculado con mediciones de RAM por
componente y no con estimaciones.

**Why this priority**: define el techo de ingresos por VM ([[ADR-003]]) y es el criterio que puede
matar el modelo de una sola VM. Depende de que (a), (b) y (c) estén corriendo.

**Independent Test**: con los componentes levantados, medir y calcular; el cálculo es verificable
con la tabla de mediciones.

**Acceptance Scenarios**:

1. **Dado** la VM real, **Cuando** se consulta su forma (arquitectura, núcleos, memoria, disco),
   **Entonces** queda registrada y se contrasta con 2 OCPU / 12 GB [EXT:Oracle Always Free].
2. **Dado** los componentes en reposo y bajo la carga del banco, **Cuando** se mide la memoria,
   **Entonces** se separa lo compartido de lo que se añade por cliente y se calcula el cupo con un
   margen declarado para el sistema operativo.

---

### User Story 5 - Prueba de descarte de Antigravity (Priority: P3)

Richard quiere evidencia, no suposición, de si Antigravity sirve como agente del bot ([[ADR-008]]).
Seis criterios, todos obligatorios; falla uno y se descarta.

**Why this priority**: el usuario lo pidió expresamente, pero la expectativa es que se descarte, y
no bloquea ninguna otra pieza.

**Independent Test**: ejecutar los seis criterios y llenar la tabla pasa/falla; no depende del canal.

**Acceptance Scenarios**:

1. **Dado** Antigravity, **Cuando** se intenta invocarlo desde un proceso sin interfaz gráfica ni
   sesión interactiva, **Entonces** el criterio 1 (y el 5) queda con veredicto y evidencia.
2. **Dado** los seis criterios, **Cuando** alguno falla, **Entonces** se registra "descartado" con la
   evidencia del primer fallo y se anota qué criterios quedaron sin probar por ese motivo.
3. **Dado** que pasa los seis, **Cuando** se corre el mismo banco que en el arnés, **Entonces** hay
   una comparación directa con los mismos datos.

---

### Edge Cases

- **El número de prueba es baneado durante el spike**: se registra como hallazgo del canal (no se
  oculta); se mantiene volumen mínimo y solo mensajes con el equipo.
- **429 del proveedor de modelos vs 429 del arnés**: los modelos `:free` tienen topes por cuenta
  [EXT:OpenRouter limites]. Los dos se distinguen en el registro, o el veredicto del arnés queda
  contaminado.
- **Modelo `:free` retirado o reemplazado a mitad del spike**: se fija el identificador exacto usado
  y se repite lo afectado.
- **La VM no tiene la forma esperada** (otra arquitectura, menos memoria, sin capacidad ARM
  disponible): se declara y todo el cálculo de cupo se rehace sobre la real.
- **Uso bajo de la VM**: con poca carga, la VM puede caer bajo los umbrales de reclamo por
  inactividad de Oracle [EXT:Oracle Always Free]; se anota el perfil observado, sin resolverlo aquí.
- **Una verificación no se puede ejecutar** (falta acceso, llave o número): queda "bloqueada" con
  causa, nunca "pasa".
- **Antigravity exige iniciar sesión por pantalla**: es evidencia directa contra los criterios 1 y 5.

## Requirements *(mandatory)*

### Functional Requirements

**Transversales**

- **FR-001**: El spike DEBE ejecutarse en la VM objetivo y su primera acción DEBE registrar la forma
  real de la VM (arquitectura, núcleos, memoria, disco).
- **FR-002**: El spike DEBE usar solo datos sintéticos y modelos `:free`; ningún dato personal real
  ni secreto DEBE entrar al contexto de un modelo (Constitución II y IV).
- **FR-003**: Ninguna prueba DEBE enviar mensajes a números fuera del equipo; el sistema solo
  responde a mensajes entrantes (Constitución III).
- **FR-004**: Cada pieza probada DEBE registrar su versión o identificador exacto (imagen, paquete,
  modelo), por el riesgo de cadena de suministro ya documentado [EXT:Ban de WhatsApp en bots 2026].
- **FR-005**: Cada verificación DEBE tener procedimiento escrito, entradas, resultado crudo y
  veredicto, de modo que otra persona pueda repetirla.

**(a) Canal**

- **FR-006**: DEBE vincularse un número de prueba y recibir en el sistema un mensaje entrante con
  contenido y remitente, y responderlo por la API.
- **FR-007**: Tras caída forzada del proceso y de la red, la instancia DEBE reconectar sin repetir
  el emparejamiento en ≤ 120 s [Adivinando: umbral a validar]; DEBE registrarse si los mensajes
  llegados durante la caída se recuperan o se pierden.
- **FR-008**: DEBE poder distinguirse un mensaje escrito por una persona desde el teléfono de uno
  enviado por la API del propio sistema.
- **FR-009**: DEBE medirse la memoria del canal en reposo y bajo una ráfaga sintética definida.

**(b) Arnés**

- **FR-010**: La lista de herramientas activas del arnés NO DEBE contener ninguna nativa, y un
  mensaje hostil que intente usar terminal, archivos o web NO DEBE ejecutarlas.
- **FR-011**: Con ≥3 conversaciones paralelas, un dato introducido en una NO DEBE aparecer en otra.
- **FR-012**: El contenedor del arnés NO DEBE tener montajes del host y su salida de red DEBE
  limitarse al proveedor de modelos y al MCP; se verifica desde dentro del contenedor.
- **FR-013**: Al superar el límite concurrente, el arnés DEBE responder 429 y el cliente DEBE
  recuperar todas las solicitudes con reintento y espera creciente, sin pérdida ni duplicado.
- **FR-014**: DEBE medirse tokens de entrada y salida por llamada en ≥20 consultas del banco, contra
  un bucle de referencia mínimo (mismas consultas, mismo modelo, mismas herramientas), y reportar la
  razón; pasa si es ≤ 2×.
- **FR-015**: DEBE reportarse p50 y p95 de latencia separando el tiempo del modelo del sobrecosto del
  arnés; el objetivo de p95 es < 15 s sobre el total.
- **FR-016**: DEBE medirse la memoria del arnés en reposo y bajo carga.

**(c) Herramientas de lectura**

- **FR-017**: Las herramientas del esquema sintético de tienda DEBEN generarse desde una descripción
  del esquema, no escribirse a mano una por una.
- **FR-018**: Cada herramienta DEBE ejecutar una consulta fija con parámetros tipados; entradas
  hostiles NO DEBEN alterar la consulta ni devolver datos fuera de lo declarado.
- **FR-019**: NO DEBE existir ninguna vía de SQL libre en la configuración final, y una escritura
  con el rol de lectura DEBE fallar.
- **FR-020**: El arnés (b) DEBE consumir estas herramientas de punta a punta; si (c) falla, se usa un
  MCP de prueba mínimo y se anota.

**(d) Cupo**

- **FR-021**: DEBE medirse la memoria por componente separando lo compartido de lo que se añade por
  cliente, en reposo y bajo carga, y calcularse el cupo con un margen declarado para el sistema.
- **FR-022**: El cupo DEBE contrastarse con **4 clientes**, la meta de la etapa de desarrollo
  (decisión de Richard, 2026-10-02). Además DEBE informar el techo de la VM (cuántos clientes caben
  antes de necesitar otra) y qué componente se agota primero, porque el negocio espera crecer y una
  sola VM será un límite temporal.

**(e) Antigravity**

- **FR-023**: DEBE llenarse una tabla de los seis criterios de [[ADR-008]] con pasa/falla/no probado
  y evidencia por fila; el criterio de términos de uso DEBE citar el texto original y registrarse como
  ficha en `vault/Fuentes/`.
- **FR-024**: Si pasa los seis, DEBE compararse con el arnés sobre el mismo banco de consultas.

**Salida**

- **FR-025**: Cada pieza (canal, arnés, herramientas, Antigravity) DEBE cerrar con veredicto
  go/no-go y, si no pasa, la alternativa activada: WAHA o BuilderBot para el canal, bucle propio para
  el arnés, MCP propio para las herramientas.
- **FR-026**: Cada veredicto DEBE registrarse como ADR nuevo que confirma o supera al original; los
  ADR existentes no se editan.
- **FR-027**: Una verificación no ejecutada DEBE figurar como "bloqueada" con su causa; el spike no
  se da por cerrado mientras haya una sin veredicto.

### Key Entities

- **Verificación**: una de las cinco (a–e); tiene procedimiento, entradas, resultado y veredicto.
- **Evidencia**: resultado crudo reproducible (mediciones, registros, citas de términos).
- **Veredicto**: pasa / falla / bloqueada, más go/no-go de la pieza y la alternativa si no pasa.
- **Banco sintético**: conjunto mínimo de consultas inventadas, común a arnés y Antigravity.
- **Cupo**: número de clientes que caben en la VM, derivado de las mediciones.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Las cinco verificaciones terminan con veredicto (pasa, falla o bloqueada con causa), cada
  una con evidencia que otra persona puede repetir.
- **SC-002**: Las cuatro piezas (canal, arnés, herramientas, Antigravity) tienen decisión go/no-go
  registrada, y toda pieza que no pasa tiene su alternativa nombrada.
- **SC-003**: El cupo de clientes por VM sale de mediciones sobre la VM real, no de estimaciones;
  se contrasta con la meta de 4 clientes y se informa el techo y el componente que lo limita.
- **SC-004**: El costo por llamada del arnés está medido sobre ≥20 consultas y expresado como razón
  contra el bucle de referencia.
- **SC-005**: La tabla de Antigravity tiene seis filas con veredicto y evidencia, o una fila de fallo
  que justifica el descarte.
- **SC-006**: Cero datos personales reales usados y cero mensajes enviados fuera del equipo durante
  todo el spike.

## Assumptions

- **VM provisional (2026-10-03, [[ADR-009]]).** El spike avanza en una VM compartida con otro proyecto y con menos memoria que la planeada; sus resultados son provisionales. V0, V4, las mediciones de memoria y V5 se repiten en la VM definitiva (tarea T047). Esto matiza FR-001: la forma real se registra en ambas VM.

- Orden de ejecución sugerido: forma de la VM → (c) → (b) → (a) → (d) → (e); (b) puede arrancar con
  un MCP de prueba mínimo si (c) no está lista.
- Se construye un **bucle de referencia mínimo** solo para medir la razón de tokens; es descartable y
  no es el plan B terminado.
- El banco sintético mínimo (~20 consultas de tienda) se define en este spike [Adivinando: tamaño];
  el banco de evals completo es de F2.
- Se prueba solo texto; grupos, audios, imágenes y estados quedan fuera.
- Los umbrales de reconexión (120 s) y el margen de memoria para el sistema son supuestos a validar
  en la ejecución; si resultan irreales se corrigen con evidencia, en un ADR.
- La evidencia numérica va en un solo archivo de resultados enlazado desde la ficha; la ubicación
  exacta se fija en el plan (Ley de Dueño Único: no se repite en otro lado).
- Antigravity se prueba con la suscripción personal de Richard, bajo su responsabilidad.
- Crecimiento: el negocio espera que los clientes aumenten con el tiempo. Este spike fija el techo
  de **una** VM; cómo crecer más allá (otra VM, otro proveedor) se decide después en un ADR, no aquí.
- Memoria por cliente: se mide con 1 número real y se proyecta a 4 con carga simulada, porque
  probablemente no haya 4 números reales durante el spike [Probable]. La proyección se declara como tal.
- **Bloqueos de entrada** ([[STATE]]): acceso a la VM (host, usuario, llave), llave de OpenRouter y un
  número de WhatsApp dedicado no VoIP. Richard no podrá comprar la línea en los próximos días, así
  que (a) queda "bloqueada" hasta entonces; (b), (c), (d) parcial y (e) no necesitan el número y
  pueden avanzar antes. Sin los demás insumos, sus verificaciones también quedan "bloqueadas".
- **Fuera de alcance**: SAS completo, gateway, cola, comandos de admin, agenda, Meta FB/IG, aspectos
  legales (F2–F8).
