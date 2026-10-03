#!/usr/bin/env python3
"""Compara modelos candidatos con consultas de tienda de dos vueltas (ADR-010). Solo biblioteca estándar.

Cada modelo responde dos consultas: un precio (debe llamar a la herramienta y citar el precio devuelto)
y un producto inexistente (la herramienta no devuelve nada: no debe inventar precio ni existencias).
El modelo puede pedir la herramienta varias veces (hasta 5 vueltas); cada vuelta es una solicitud y cuenta
contra la cuota diaria del proveedor. Los resultados de la herramienta son fijos: no usa la Toolbox.

  OPENROUTER_API_KEY=... python comparar_modelos.py --modelos a:free b:free [--repeticiones 1]

La llave se lee de OPENROUTER_API_KEY o de spike/.env; no se imprime.
Salida: salida/comparacion-<fecha>.json y un resumen por pantalla.
"""
import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from runner import post_chat  # noqa: E402

URL = "https://openrouter.ai/api/v1/chat/completions"
SISTEMA = (AQUI / "prompt_sistema.txt").read_text(encoding="utf-8").strip()
HERRAMIENTA = {"type": "function", "function": {
    "name": "catalogo_buscar",
    "description": "Busca productos activos por nombre o categoría. Devuelve hasta 10 coincidencias con "
                   "código (sku), nombre, categoría y precio. Si no devuelve nada, el producto no existe.",
    "parameters": {"type": "object", "properties": {"texto": {"type": "string",
                   "description": "Texto corto a buscar, por ejemplo 'polera'."}}, "required": ["texto"]}}}

ESCENARIOS = [
    {"id": "precio", "texto": "¿Cuánto cuesta la polera negra talla M?",
     "resultado": '[{"sku":"POL-NEG-M","nombre":"Polera negra talla M","categoria":"poleras","precio":8990.00}]',
     "exige": ["8990", "8.990"], "prohibe": []},
    {"id": "inexistente", "texto": "¿Tienen sombreros de paja? ¿A cuánto?",
     "resultado": "[]",
     "exige": [], "prohibe": ["$", "clp", "pesos"]},
]


def leer_llave():
    llave = os.environ.get("OPENROUTER_API_KEY", "")
    env = AQUI.parent / ".env"
    if not llave and env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            if linea.startswith("OPENROUTER_API_KEY="):
                llave = linea.split("=", 1)[1].strip().strip("\"'")
    if not llave:
        raise SystemExit("falta OPENROUTER_API_KEY (variable de entorno o spike/.env)")
    return llave


def solicitud(modelo, mensajes, llave):
    cuerpo = {"model": modelo, "stream": False, "tools": [HERRAMIENTA], "tool_choice": "auto",
              "messages": mensajes}
    r = post_chat(URL, cuerpo, llave, {}, 2, 3.0, "proveedor-directo")
    msg, uso = None, {}
    if r["datos"]:
        try:
            msg = r["datos"]["choices"][0]["message"]
            uso = r["datos"].get("usage") or {}
        except (KeyError, IndexError, TypeError):
            pass
    return {"mensaje": msg, "error": r["error"], "tiempo_s": r["tiempo_s"],
            "eventos_429": len(r["eventos_429"]), "tokens": uso.get("total_tokens")}


def correr(modelo, esc, llave, max_vueltas=5):
    """Sigue el bucle del agente: mientras el modelo pida herramientas, se le devuelve el resultado fijo."""
    mensajes = [{"role": "system", "content": SISTEMA}, {"role": "user", "content": esc["texto"]}]
    ficha = {"modelo": modelo, "escenario": esc["id"], "solicitudes": 0, "llamadas_herramienta": 0,
             "argumentos": [], "tiempo_s": 0.0, "tokens": 0, "errores_429": 0, "error": None,
             "respuesta": None, "veredicto": "falla"}
    for _ in range(max_vueltas):
        v = solicitud(modelo, mensajes, llave)
        ficha["solicitudes"] += 1
        ficha["tiempo_s"] = round(ficha["tiempo_s"] + v["tiempo_s"], 2)
        ficha["tokens"] += v["tokens"] or 0
        ficha["errores_429"] += v["eventos_429"]
        if v["error"] or not v["mensaje"]:
            ficha["error"] = v["error"] or "sin mensaje"
            return ficha
        llamadas = v["mensaje"].get("tool_calls") or []
        if not llamadas:
            texto = (v["mensaje"].get("content") or "").strip()
            ficha["respuesta"] = texto[:240]
            bajo = texto.lower()
            ok = bool(texto) and ficha["llamadas_herramienta"] > 0                 and (not esc["exige"] or any(x in bajo for x in esc["exige"]))                 and not any(x in bajo for x in esc["prohibe"])
            ficha["veredicto"] = "pasa" if ok else "falla (respuesta incorrecta o sin usar la herramienta)"
            return ficha
        mensajes.append({"role": "assistant", "content": v["mensaje"].get("content") or "", "tool_calls": llamadas})
        for ll in llamadas:
            ficha["llamadas_herramienta"] += 1
            ficha["argumentos"].append(ll["function"].get("arguments"))
            mensajes.append({"role": "tool", "tool_call_id": ll.get("id", "call_0"), "content": esc["resultado"]})
    ficha["error"] = f"más de {max_vueltas} vueltas sin respuesta final"
    return ficha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelos", nargs="+", required=True)
    ap.add_argument("--repeticiones", type=int, default=1)
    args = ap.parse_args()
    llave = leer_llave()
    fichas = []
    salida = AQUI / "salida"
    salida.mkdir(exist_ok=True)
    archivo = salida / f"comparacion-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    for modelo in args.modelos:
        for _ in range(args.repeticiones):
            for esc in ESCENARIOS:
                f = correr(modelo, esc, llave)
                fichas.append(f)
                # se guarda tras cada consulta: un fallo posterior no pierde lo ya gastado de la cuota
                archivo.write_text(json.dumps(fichas, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"{modelo} | {esc['id']}: {f['veredicto']} | {f['solicitudes']} solicitudes, "
                      f"{f['llamadas_herramienta']} herramientas, {f['tiempo_s']}s | "
                      f"{(f['respuesta'] or f['error'] or '')[:100]!r}")
    print("\nResumen por modelo (tiempo total de la consulta, solo las que pasan):")
    for modelo in args.modelos:
        propias = [f for f in fichas if f["modelo"] == modelo]
        buenas = [f["tiempo_s"] for f in propias if f["veredicto"] == "pasa"]
        med = f"mediana {statistics.median(buenas):.1f}s, máximo {max(buenas):.1f}s" if buenas else "sin respuestas válidas"
        gasto = sum(f["solicitudes"] for f in propias)
        print(f"  {modelo}: {len(buenas)}/{len(propias)} pasan; {med}; {gasto} solicitudes gastadas")
    print("guardado en", archivo.relative_to(AQUI.parent.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
