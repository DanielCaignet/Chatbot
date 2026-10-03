#!/usr/bin/env python3
"""T015 (SPEC-001, FR-013, R6): 12 solicitudes simultáneas contra el tope de 10 del api_server.

Corre en la VM con Hermes arriba. Solo biblioteca estándar.

  prueba_429.py [--endpoint chat|runs] [--solicitudes 12] [--reintentos 6] [--espera 2]

--endpoint chat  (por defecto) manda cada solicitud a /v1/chat/completions con reintento y espera
                 creciente ante 429, y comprueba que las 12 terminan, cada una con su propia respuesta,
                 sin pérdida ni duplicado.
--endpoint runs  manda las solicitudes a POST /v1/runs sin reintento y solo cuenta los 429: sirve para
                 anotar si el tope aplica también ahí (la documentación dice que sí; esto lo mide).

Que haya 429 depende de que las ejecuciones se solapen: si el modelo responde tan rápido que no llegan
a 10 en vuelo, no habrá 429 y el resultado será "no concluyente", no "pasa".

Salida: salida/429-<endpoint>-<fecha>.json. Código de salida: 0 pasa, 1 falla, 3 no concluyente.
"""
import argparse
import json
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "bench"))
sys.path.insert(0, str(AQUI))
from runner import post_chat  # noqa: E402  reutiliza el reintento con espera creciente de T008
import cliente  # noqa: E402


def una_chat(n, marca, args, resultados):
    ficha = f"ECO{n:02d}"
    cuerpo = {"model": "hermes-agent", "stream": False,
              "messages": [{"role": "user",
                            "content": f"Responde únicamente con esta palabra, sin nada más: {ficha}"}]}
    r = post_chat(cliente.base_url() + "/v1/chat/completions", cuerpo, cliente.leer_llave(),
                  {"X-Hermes-Session-Id": f"r429-{marca}-{n}"}, args.reintentos, args.espera, "arnes")
    texto = None
    if r["datos"]:
        try:
            texto = r["datos"]["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            pass
    resultados[n] = {"ficha": ficha, "eventos_429": r["eventos_429"], "error": r["error"], "texto": texto}


def una_run(n, marca, args, resultados):
    estado, crudo, error = cliente.pedir(
        "POST", "/v1/runs",
        {"input": f"Responde únicamente con esta palabra: ECO{n:02d}", "session_id": f"r429-{marca}-{n}"})
    resultados[n] = {"estado": estado, "error": error, "cuerpo": crudo[:150]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", choices=["chat", "runs"], default="chat")
    ap.add_argument("--solicitudes", type=int, default=12)
    ap.add_argument("--reintentos", type=int, default=6)
    ap.add_argument("--espera", type=float, default=2.0)
    args = ap.parse_args()

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    resultados, hilos = {}, []
    lanzar = una_chat if args.endpoint == "chat" else una_run
    puerta = threading.Barrier(args.solicitudes)

    def trabajo(n):
        puerta.wait()  # arrancan todas a la vez
        lanzar(n, marca, args, resultados)

    t0 = time.monotonic()
    for n in range(args.solicitudes):
        h = threading.Thread(target=trabajo, args=(n,))
        h.start()
        hilos.append(h)
    for h in hilos:
        h.join()
    duracion = round(time.monotonic() - t0, 1)

    salida = AQUI / "salida"
    salida.mkdir(exist_ok=True)
    archivo = salida / f"429-{args.endpoint}-{marca}.json"

    if args.endpoint == "runs":
        con_429 = [n for n, r in resultados.items() if r["estado"] == 429]
        aceptadas = [n for n, r in resultados.items() if r["estado"] in (200, 202)]
        veredicto = "pasa" if con_429 else "no concluyente"
        archivo.write_text(json.dumps({"endpoint": "runs", "veredicto": veredicto, "respuestas_429": len(con_429),
                                       "aceptadas": len(aceptadas), "detalle": resultados},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"/v1/runs: {len(aceptadas)} aceptadas, {len(con_429)} con 429 de {args.solicitudes} | {duracion}s")
        print("veredicto:", veredicto, "(el tope aplica a /v1/runs)" if con_429 else "(no se vio 429)")
        return 0 if con_429 else 3

    con_429 = [n for n, r in resultados.items() if r["eventos_429"]]
    perdidas = [n for n, r in resultados.items() if r["error"] or r["texto"] is None]
    fichas = [r["ficha"] for r in resultados.values()]
    propias = [n for n, r in resultados.items() if r["texto"] and r["ficha"] in r["texto"]]
    cruzadas = [n for n, r in resultados.items()
                if r["texto"] and any(f in r["texto"] for f in fichas if f != r["ficha"])]
    duplicadas = len(propias) != len(set(propias)) or len(set(fichas)) != len(fichas)
    max_espera = max((e["espera_s"] for r in resultados.values() for e in r["eventos_429"]), default=0)
    recuperadas = [n for n in con_429 if n not in perdidas]

    if perdidas or cruzadas or duplicadas:
        veredicto = "falla"
    elif not con_429:
        veredicto = "no concluyente"
    else:
        veredicto = "pasa"
    archivo.write_text(json.dumps({
        "endpoint": "chat", "veredicto": veredicto, "solicitudes": args.solicitudes,
        "con_429": len(con_429), "recuperadas_tras_429": len(recuperadas), "perdidas": perdidas,
        "respuestas_cruzadas": cruzadas, "espera_maxima_s": max_espera, "duracion_s": duracion,
        "detalle": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"/v1/chat/completions: {args.solicitudes} solicitudes en {duracion}s")
    print(f"  con al menos un 429: {len(con_429)} | recuperadas tras 429: {len(recuperadas)} | perdidas: {len(perdidas)}")
    print(f"  respuestas propias: {len(propias)}/{args.solicitudes} | cruzadas: {len(cruzadas)} | duplicadas: {'sí' if duplicadas else 'no'}")
    print(f"  espera máxima entre reintentos: {max_espera}s")
    print("veredicto:", veredicto)
    if veredicto == "no concluyente":
        print("  no hubo 429: las ejecuciones no llegaron a solaparse 10 a la vez. Repetir con más solicitudes (--solicitudes 20).")
    return {"pasa": 0, "falla": 1}.get(veredicto, 3)


if __name__ == "__main__":
    sys.exit(main())
