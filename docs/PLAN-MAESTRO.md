# Plan: chatbot de ventas genérico multi-cliente ("Chatbot Richard")

## Contexto
Daniel quiere vender a negocios pequeños (tienda, peluquería, gimnasio…) un chatbot de ventas en Docker.
- **Infraestructura:** una sola Oracle VM Always Free ARM A1, con un stack aislado por cliente.
- **Canales:** WhatsApp de clientes vía Baileys (decisión del usuario, riesgo aceptado), FB/IG vía API Meta y WhatsApp del admin (handoff, comandos, alertas y agenda).
- **Alcance del agente:** toma el pedido completo. El procedimiento es siempre el mismo y solo cambia el destino: descontar stock o agendar en Google Calendar.
- **Núcleo, la capa SAS:** el arnés de acceso a la BD que impide inventar precios, stock, horarios o SKUs. Debe ser genérica: descubre tablas del cliente o usa un Postgres propio con plantilla por rubro.
- **Carga:** aguantar ~100 conversaciones al día por negocio sin caerse a media jornada.
- **Directorio:** `D:\Richard\Chatbot Richard`, vacío.

## Referencias externas consultadas (y qué cambian)
| Hallazgo | Fuente | Efecto en el plan |
|---|---|---|
| Always Free A1 hoy = 1.500 OCPU-h + 9.000 GB-h/mes, **equivale a 2 OCPU / 12 GB** (antes 4/24). Se reclama por inactividad solo si CPU p95, red **y** memoria están bajo 20 % durante 7 días. 10 TB de egreso al mes. [Seguro] | docs.oracle.com, Always Free Resources | Capacidad a la mitad de lo supuesto. F0 verifica `nproc`/`free -g` (si la VM es antigua, puede conservar 4/24 [Adivinando]). Con varios stacks, el riesgo de reclamo es bajo |
| Bots Baileys que **solo responden**: <2 % de ban en 12 meses. Los que escriben primero a desconocidos: 15–30 % [Probable, fuente de blog]. En 2026 WhatsApp cuenta los **mensajes sin respuesta** en una ventana móvil. Hubo un fork malicioso de Baileys en npm ("lotusbail") que robaba sesiones. [Probable] | lumadock.com, achiya-automation.com, checkleaked.cc | Regla dura: cero mensajes salientes que no sean respuesta (salvo alertas al admin). Se fija `@whiskeysockets/baileys` oficial con lockfile. Número dedicado, no VoIP |
| **Evolution API**: Baileys + Cloud API oficial en una sola interfaz, multi-instancia, integración con Chatwoot. Licencia Apache-2.0 más una condición: avisar en el sistema que se usa Evolution API y no quitar su logo del frontend. [Seguro] | github.com/EvolutionAPI (LICENSE) | **Adoptar como capa de canal** en vez de escribir el gateway Baileys: da la ruta a Cloud API sin reescribir. Cumplir el aviso en la doc o configuración del admin |
| **WAHA** (7,5k★, núcleo gratis y Plus de pago) y **BuilderBot** (3k★, MIT, comunidad hispana) | GitHub | Alternativas si Evolution no rinde en el spike |
| **Chatwoot** (MIT): bandeja omnicanal con FB/IG y WhatsApp, handoff humano, multi-cuenta [Seguro en la licencia; Probable que pese >1,5 GB de RAM] | github.com/chatwoot | Opcional en F7 como bandeja web del admin y como vía a FB/IG. En v1, el admin opera por WhatsApp |
| **Hermes Agent** (250k★): `api_server` compatible con OpenAI, sesiones con `X-Hermes-Session-Id`, `max_concurrent_runs` por defecto 10 que responde **HTTP 429** al llenarse. Está pensado como agente personal con terminal y archivos. [Seguro] | hermes-agent.nousresearch.com (api-server, security) | La cola debe hacer backoff ante 429. Cliente final = entrada no confiable: **todas las toolsets nativas apagadas** en `api_server` y solo la MCP del SAS (spike confirma que se puede). Contenedor sin montajes del host y egreso filtrado |
| **MCP Toolbox for Databases** (Google): herramientas declaradas en `tools.yaml` con **SQL parametrizado fijo** para Postgres, MySQL, SQLite y más | github.com/googleapis/genai-toolbox | Candidato para servir las herramientas de lectura del SAS: `semantic.yaml` → genera `tools.yaml`. **Nunca** el prebuilt con `execute_sql` |
| WrenAI (capa semántica MDL) y Vanna (MIT, text-to-SQL libre) | GitHub | WrenAI solo como referencia del formato de `semantic.yaml`. Vanna se descarta: SQL libre contradice el diseño |
| Casos de alucinación con costo: **Air Canada** (2024, el tribunal obligó a la aerolínea a cumplir una política que inventó su bot) y **Chevrolet "Tahoe a USD 1"** (2023) [Seguro] | conocimiento público | Valida el núcleo: las cifras y condiciones las pone el código desde plantillas; el modelo nunca redacta un número |
| Precios por 1M de tokens. **DeepSeek Flash** fuera de hora punta: entrada USD 0,15, entrada en caché 0,003, salida 0,60 (la hora punta UTC cae fuera del horario comercial de Chile); concurrencia 2.500. **Gemini 3.1 Flash-Lite** de pago: 0,25 / caché 0,025 / 1,50, sin entrenar con los datos. El tier gratis prohíbe datos personales. [Seguro] | api-docs.deepseek.com, ai.google.dev | Gimnasio (2.000 llamadas/día, 3,5k de entrada y 200 de salida): **DeepSeek ~USD 14/mes con caché (~39 sin caché); Gemini ~USD 33 (~70)**. Esto corrige mi estimación anterior de 5–20. DeepSeek procesa en China: es transferencia internacional (Ley 21.719) y va declarada en el contrato |
| LLM local en A1: un 7B Q4 genera ~8–12 tok/s con **4** OCPU [Probable]. Con 2 OCPU, peor | blog.easecloud.io, amperecomputing.com | Se descarta el modelo local para el agente. A lo más se usa para embeddings del catálogo |

## Decisiones
| Tema | Decisión |
|---|---|
| Canal | **Evolution API** (motor Baileys) detrás de la interfaz `Canal`. Cloud API disponible en la misma pieza |
| Arnés | **Hermes Agent** vía `api_server`, solo con herramientas MCP del SAS |
| Tenancy | Un `docker compose -p <cliente>` por negocio (Hermes + SAS + Postgres propio si aplica). Compartido: Evolution (una instancia por número), Traefik y el gateway-cola (particionado por cliente) para ahorrar RAM en 12 GB |
| BD | Postgres propio con plantilla de rubro **o** adaptador a la BD del cliente con descubrimiento de esquema |
| LLM, desarrollo y pruebas | **Modelos `:free` de OpenRouter** (decisión del usuario), solo con datos sintéticos. El tier gratis no admite datos personales y tiene topes globales por cuenta, así que los evals se dosifican y la cola respeta el 429 |
| LLM, producción | Por decidir antes de salir al mercado. Recomendación vigente: BYOK de pago (DeepSeek Flash principal y Gemini Flash-Lite de respaldo). El proveedor es intercambiable por configuración (`LLM_PROFILE=dev-free \| prod-byok`) |
| Antigravity | **Prueba de descarte** en F1(e): confirmar con evidencia si sirve o no como agente del bot. Se descarta si falla cualquiera de estos criterios |

## Arquitectura
```
Evolution API ──webhook──> gateway (TS): debounce, admin, takeover ──> cola pg-boss (por chat)
                                                                         │
                                         worker ──> Hermes api_server (cliente X) ──MCP──> SAS (cliente X)
                                           │                                               ├─ Postgres / BD cliente
                                           └─> verificador SAS (ledger del turno) <────────┴─ Google Calendar (OAuth)
```

### Capa SAS (núcleo)
1. **Descubrimiento**: se introspecciona `information_schema` y sale un borrador de `semantic.yaml` (entidades, grano, clave, campos tipados `id|cat|texto|numero|dinero|stock|fecha`, formato inspirado en el MDL de WrenAI). El LLM puede proponer etiquetas; el admin aprueba y el catálogo queda congelado.
2. **Herramientas tipadas con SQL fijo parametrizado**: `catalogo_buscar`, `item_obtener` y `disponibilidad` se generan como `tools.yaml` de MCP Toolbox, o en el MCP propio si el spike lo descarta. Un rol de solo lectura para leer y otro limitado a las tablas declaradas para escribir.
3. **Acciones por rubro** (`stock_decrement | calendar_booking | registro`): `preparar → confirmación al cliente → confirmar`. El texto de confirmación lo arma el código desde la salida de la herramienta. Cada pedido tiene clave de idempotencia y la escritura es transaccional.
4. **Anclaje**: todo identificador debe venir del texto del usuario o de un resultado previo.
5. **Verificación de salida**: cada número, precio, SKU, fecha u hora de la respuesta tiene que estar en el `sas_ledger` del turno. Si falla, 1 regeneración; luego plantilla segura o handoff.

### Resiliencia
- Cola pg-boss persistente, serializada por chat y con N chats en paralelo.
- Debounce de 3–5 s, timeouts, backoff ante 429 de Hermes o del proveedor, y cadena de modelos de respaldo.
- Si todo falla: aviso al admin y al cliente "te respondemos en un momento".
- Healthchecks y `restart: unless-stopped`.

### Admin
- Lista blanca de números. Comandos `/pausar /reanudar /tomar /soltar /stock /reporte /agendar`.
- **Takeover natural**: si el dueño escribe desde su teléfono vinculado (`fromMe`), el bot se calla en ese chat por N horas.
- Alertas: venta cerrada, cita agendada, fallas y desconexión o ban.

## Estructura del repo
```
gateway/   TS: webhooks Evolution/Meta, cola, admin, worker, cliente Hermes
sas/       Python MCP: discovery, semantic→tools.yaml, acciones, ledger, verificador
hermes/    config.yaml plantilla (toolsets nativas off), SOUL base, skills (inventario, comunicación, ventas)
rubros/    tienda | peluqueria | gimnasio: schema.sql, semantic.yaml, SOUL.md
deploy/    compose.shared.yml (traefik, evolution, gateway), compose.tenant.yml, tenant-new.sh, backups
evals/     banco por rubro: alucinación, pedidos, takeover
```

## Reutilización interna
> Corregido 2026-10-01: estas rutas están en el PC de Daniel (proyectos de DataSeed) y **no viajan
> en este repo**. Para usarlas, hay que pedirle a Daniel el código puntual o reimplementar el patrón
> a partir de la descripción.

- Capa semántica: `D:\Dataseed\Agent Factory\mcp-mercado-publico\src\mp_mcp\{semantic,tools,server}.py` y `D:\Dataseed\CristalChile-Maqueta\src\semantica.py`
- Guardas SQL, anclaje y verificación de cifras: `CristalChile-Maqueta\src\{ui_sql,ui_plan,ui_conversa}.py`
- Hermes en Docker y egreso filtrado: `CristalChile-Maqueta\vps\agente-maqueta\{docker-compose.yml,config.yaml,SOUL.md,filtro\filtro_egreso.py}`
- Rate limit de Hermes: `D:\Dataseed\data_seed\api\demo-chat.js`
- OAuth Google: `Agent Factory\PROC-001-agent-vault-google-workspace.md`
- Evals: `banco-agente\banco_specs.js`
- Ley 21.719: `PROC-002-ley-21719-proteccion-datos.md`
- Lecciones previas: `Agent Factory\decisiones.md` (D-004, D-012, D-018, D-023)
- Principios: `D:\Dataseed\Agent Engine\CONSTITUCION.md` A1/A4/A5/A6

## Fases (un spec de Spec Kit cada una)
- **F0 Montaje**: `/full-autodev chatbot-richard`, `git init` y constitución. Verificar el tamaño real de la VM.
- **F1 Spike (gate, en la VM)**:
  - (a) Evolution + Baileys: conexión, reconexión, `fromMe` y RAM.
  - (b) Hermes `api_server` con solo MCP: sesiones paralelas, 429, **tokens por llamada** (el overhead del prompt de Hermes define el costo real) y RAM.
  - (c) MCP Toolbox con `tools.yaml` generado.
  - (d) RAM por stack, de donde sale el cupo de clientes por VM.
  - (e) Prueba de descarte de Antigravity. Criterios, todos obligatorios:
    1. Recibe un mensaje y devuelve una respuesta de forma programática, sin interfaz gráfica, desde el worker.
    2. Atiende ≥3 conversaciones concurrentes con contexto aislado.
    3. p95 <15 s.
    4. Usa la MCP del SAS.
    5. Corre 24/7 en Linux ARM, o accesible desde la VM, sin sesión interactiva.
    6. Sus términos permiten atender a terceros.
    Resultado: tabla pasa/falla con evidencia en el vault. Si pasa los seis, se compara con Hermes sobre el mismo banco de evals.
  - Todo el spike corre con OpenRouter `:free`.
  - Si Hermes da más de ~2× los tokens de un bucle propio o no permite apagar sus toolsets: bucle propio en `worker`.
- **F2 SAS**: discovery, semantic, herramientas, ledger, verificador y evals.
- **F3 MVP tienda**: Evolution → gateway → cola → Hermes → SAS, con `stock_decrement`.
- **F4 Admin**: comandos, takeover y alertas.
- **F5 Agenda**: OAuth Google y `calendar_booking` (peluquería y gimnasio).
- **F6 Aprovisionamiento**: `tenant-new.sh`, backups fuera de la VM (Object Storage) y monitoreo.
- **F7 Meta FB/IG**: Graph API (app review y verificación de negocio) o Chatwoot.
- **F8 Legal**: contrato de encargado (Ley 21.719, incluida la transferencia a DeepSeek), retención y auditoría.

Anti-slop en cada commit con código. **`/thermos` solo cuando el usuario lo pida explícitamente**; ningún subagente se dispara solo.

## Reglas de trabajo (se guardan en la memoria al empezar)
- Investigar referencias externas (repos y comunidad) antes de proponer un plan propio.
- Hacer las búsquedas yo mismo, sin subagentes.
- Thermos y cualquier subagente, solo a pedido del usuario.

## Verificación
- **Evals con preguntas trampa** (precio o stock inexistente, SKU inventado, horario ocupado): 0 cifras sin respaldo en el ledger.
- **Carga**: 100 conversaciones en 10 h por cliente, con 3 clientes a la vez en la VM real. Exige 0 mensajes perdidos, p95 <15 s y reinicio a mitad de la carga sin pérdida.
- **E2E**: compra en tienda (descuenta stock), takeover desde el teléfono, reserva en peluquería (evento en Calendar), alerta al admin.
- **Backups**: restauración en un stack nuevo.

## Fuentes
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://raw.githubusercontent.com/EvolutionAPI/evolution-api/main/LICENSE
- https://github.com/devlikeapro/waha · https://github.com/codigoencasa/builderbot · https://github.com/chatwoot/chatwoot · https://github.com/WhiskeySockets/Baileys
- https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server · https://hermes-agent.nousresearch.com/docs/user-guide/security · https://lumadock.com/tutorials/hermes-whatsapp-baileys-gateway
- https://achiya-automation.com/en/blog/whatsapp-spam-detection-2026/ · https://whatsapp.checkleaked.cc/blog/avoid-whatsapp-ban
- https://github.com/googleapis/genai-toolbox · https://github.com/Canner/WrenAI · https://github.com/vanna-ai/vanna
- https://api-docs.deepseek.com/quick_start/pricing · https://ai.google.dev/gemini-api/docs/pricing · https://ai.google.dev/gemini-api/terms · https://openrouter.ai/docs/api-reference/limits
- https://amperecomputing.com/blogs/llama3-on-Ampere-based-OCI-A1 · https://blog.easecloud.io/ai-cloud/launch-oracle-cloud-llms-in/
