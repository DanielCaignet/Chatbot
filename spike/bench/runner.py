#!/usr/bin/env python3
"""Runner del banco sintético (T008, SPEC-001). Solo biblioteca estándar de Python.

Ejecuta cada consulta de banco.json contra un endpoint compatible con OpenAI y guarda,
por consulta: tiempo total, tokens, reintentos por 429 y el origen de cada 429.

Ejemplo (contra el arnés):
  BENCH_API_KEY=... python runner.py --url http://127.0.0.1:8642/v1 \
      --modelo hermes-agent --etiqueta hermes --destino arnes --salida salida/hermes.json

La llave va solo en la variable BENCH_API_KEY, nunca como argumento (quedaría en el historial).
También se usa como biblioteca: `correr()` y `post_chat()` los importa baseline/bucle.py.
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MAX_ESPERA_S = 60.0
TIMEOUT_S = 120


def origen_429(cuerpo, destino):
    """Clasifica un 429. [Adivinando]: heurística a validar en V3 (T015).

    'proveedor-directo': el endpoint es el propio proveedor de modelos.
    'arnes': hay un arnés delante; si el cuerpo nombra al proveedor, el 429 viene de él.
    """
    if destino == "proveedor-directo":
        return "proveedor"
    texto = (cuerpo or "").lower()
    if any(palabra in texto for palabra in ("openrouter", "upstream", "provider")):
        return "proveedor"
    return "arnes"


def post_chat(endpoint, cuerpo, llave, cabeceras, reintentos, espera_inicial, destino):
    """POST de chat/completions con reintento y espera creciente ante 429.

    Devuelve {"datos", "error", "eventos_429", "tiempo_s"}; tiempo_s es el de la llamada
    final, sin las esperas de reintento (esas van en eventos_429).
    """
    carga = json.dumps(cuerpo).encode("utf-8")
    eventos_429 = []
    for intento in range(reintentos + 1):
        req = urllib.request.Request(endpoint, data=carga, method="POST")
        req.add_header("Content-Type", "application/json")
        for nombre, valor in cabeceras.items():
            req.add_header(nombre, valor)
        if llave:
            req.add_header("Authorization", f"Bearer {llave}")
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                datos = json.load(r)
            return {"datos": datos, "error": None, "eventos_429": eventos_429,
                    "tiempo_s": time.monotonic() - t0}
        except urllib.error.HTTPError as e:
            texto_err = e.read().decode("utf-8", "replace")[:300]
            if e.code == 429:
                espera = min(MAX_ESPERA_S, espera_inicial * 2 ** intento)
                retry = e.headers.get("Retry-After")
                if retry and retry.isdigit():
                    espera = min(MAX_ESPERA_S, max(espera, float(retry)))
                reintenta = intento < reintentos
                eventos_429.append({"intento": intento + 1,
                                    "origen": origen_429(texto_err, destino),
                                    "espera_s": espera if reintenta else 0})
                if reintenta:
                    time.sleep(espera)
                    continue
            return {"datos": None, "error": f"HTTP {e.code}: {texto_err}",
                    "eventos_429": eventos_429, "tiempo_s": time.monotonic() - t0}
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            return {"datos": None, "error": f"{type(e).__name__}: {e}",
                    "eventos_429": eventos_429, "tiempo_s": time.monotonic() - t0}
    return {"datos": None, "error": "sin respuesta", "eventos_429": eventos_429, "tiempo_s": 0.0}


def responder_http(url, modelo, llave, reintentos, espera_inicial, destino):
    """Responder para un endpoint compatible con OpenAI (el arnés o el proveedor)."""
    endpoint = url.rstrip("/") + "/chat/completions"

    def responder(texto, sesion):
        cuerpo = {"model": modelo, "stream": False,
                  "messages": [{"role": "user", "content": texto}]}
        r = post_chat(endpoint, cuerpo, llave, {"X-Hermes-Session-Id": sesion},
                      reintentos, espera_inicial, destino)
        salida = {"respuesta": None, "prompt_tokens": None, "completion_tokens": None,
                  "tiempo_modelo_s": None, "vueltas": None,
                  "eventos_429": r["eventos_429"], "error": r["error"]}
        if r["datos"]:
            uso = r["datos"].get("usage") or {}
            salida["prompt_tokens"] = uso.get("prompt_tokens")
            salida["completion_tokens"] = uso.get("completion_tokens")
            try:
                salida["respuesta"] = r["datos"]["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                salida["error"] = "respuesta sin choices[0].message.content"
        return salida

    return responder


def cargar_banco(ruta):
    banco = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if not banco.get("consultas"):
        raise SystemExit(f"banco vacío o sin 'consultas': {ruta}")
    return banco


def correr(banco, responder, etiqueta, pausa_s=0.0, limite=None):
    """Ejecuta el banco con `responder(texto, sesion) -> dict` y devuelve la lista de resultados."""
    resultados = []
    consultas = banco["consultas"][:limite] if limite else banco["consultas"]
    for c in consultas:
        t0 = time.monotonic()
        r = responder(c["texto"], f"bench-{etiqueta}-{c['id']}")
        total = time.monotonic() - t0
        esperas = sum(e.get("espera_s", 0) for e in r.get("eventos_429", []))
        resultados.append({
            "id": c["id"], "grupo": c["grupo"],
            "tiempo_total_s": round(total, 3),
            "espera_429_s": round(esperas, 3),
            "tiempo_sin_esperas_s": round(max(total - esperas, 0), 3),
            "tiempo_modelo_s": r.get("tiempo_modelo_s"),
            "prompt_tokens": r.get("prompt_tokens"),
            "completion_tokens": r.get("completion_tokens"),
            "vueltas": r.get("vueltas"),
            "eventos_429": r.get("eventos_429", []),
            "error": r.get("error"),
            "respuesta": r.get("respuesta"),
        })
        if pausa_s:
            time.sleep(pausa_s)
    return resultados


def percentil(valores, p):
    """Percentil por rango más cercano. Con ~20 muestras, p95 es la 19.ª más lenta."""
    if not valores:
        return None
    ordenados = sorted(valores)
    return round(ordenados[max(0, math.ceil(p / 100 * len(ordenados)) - 1)], 3)


def promedio(valores):
    return round(sum(valores) / len(valores), 1) if valores else None


def resumir(resultados):
    ok = [r for r in resultados if not r["error"]]
    con_tokens = [r for r in ok if r["prompt_tokens"] is not None]
    eventos = [e for r in resultados for e in r["eventos_429"]]
    return {
        "consultas": len(resultados),
        "errores": len(resultados) - len(ok),
        "p50_total_s": percentil([r["tiempo_total_s"] for r in ok], 50),
        "p95_total_s": percentil([r["tiempo_total_s"] for r in ok], 95),
        "p50_sin_esperas_s": percentil([r["tiempo_sin_esperas_s"] for r in ok], 50),
        "p95_sin_esperas_s": percentil([r["tiempo_sin_esperas_s"] for r in ok], 95),
        "prompt_tokens_prom": promedio([r["prompt_tokens"] for r in con_tokens]),
        "completion_tokens_prom": promedio([r["completion_tokens"] for r in con_tokens]),
        "consultas_con_tokens": len(con_tokens),
        "n429_proveedor": sum(1 for e in eventos if e["origen"] == "proveedor"),
        "n429_arnes": sum(1 for e in eventos if e["origen"] == "arnes"),
    }


def guardar(salida, etiqueta, banco, modelo, resultados):
    ruta = Path(salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    doc = {"etiqueta": etiqueta, "modelo": modelo, "banco_version": banco.get("version"),
           "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "resumen": resumir(resultados), "resultados": resultados}
    ruta.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc["resumen"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", required=True, help="base del endpoint, p. ej. http://127.0.0.1:8642/v1")
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--etiqueta", required=True, help="nombre de la corrida: hermes, baseline…")
    ap.add_argument("--destino", choices=["arnes", "proveedor-directo"], default="arnes")
    ap.add_argument("--banco", default=str(AQUI / "banco.json"))
    ap.add_argument("--salida", required=True)
    ap.add_argument("--reintentos", type=int, default=5)
    ap.add_argument("--espera-inicial", type=float, default=2.0)
    ap.add_argument("--pausa", type=float, default=0.0, help="segundos entre consultas (topes de :free)")
    ap.add_argument("--limite", type=int, default=None, help="solo las N primeras (prueba rápida)")
    a = ap.parse_args()

    banco = cargar_banco(a.banco)
    llave = os.environ.get("BENCH_API_KEY", "")
    responder = responder_http(a.url, a.modelo, llave, a.reintentos, a.espera_inicial, a.destino)
    resultados = correr(banco, responder, a.etiqueta, a.pausa, a.limite)
    resumen = guardar(a.salida, a.etiqueta, banco, a.modelo, resultados)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(f"guardado en {a.salida}", file=sys.stderr)


if __name__ == "__main__":
    main()
