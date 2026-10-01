---
tipo: agent-index
proyecto: "chatbot-richard"
actualizado: 2026-10-01
---

# AGENT-INDEX — chatbot-richard

> Superficie de orientacion del agente. Junto con `STATE.md` son los **unicos dos
> archivos** que se leen al arrancar. Todo lo demas se alcanza por enlaces, bajo
> demanda. Mantener este archivo por debajo de 60 lineas: si crece, el detalle va a un MOC.

## Entradas
- [[00 - Indice de Specs]] — que se esta construyendo y en que estado
- [[01 - Indice de Conceptos]] — vocabulario del dominio
- [[02 - Indice de Decisiones]] — por que las cosas son como son
- [[03 - Indice de Fuentes]] — documentos externos ya destilados

## Como consultar antes de responder
```bash
graphify query "<pregunta>"        # subgrafo acotado
graphify affected "<nodo>"          # que queda obsoleto si esto cambia
graphify path "<A>" "<B>"           # como se relacionan dos cosas
graphify explain "<nodo>"           # que es un nodo y sus vecinos
```

## Invariantes
Viven en `.specify/memory/constitution.md`. No se copian aca.

## Perfil
`software`