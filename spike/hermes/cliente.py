#!/usr/bin/env python3
"""Cliente mínimo del api_server de Hermes para las pruebas T011–T015 (SPEC-001). Solo biblioteca estándar.

  cliente.py get /v1/toolsets
  cliente.py chat --sesion <id> --texto "<mensaje>" [--sistema ruta.txt]

Imprime una línea JSON. `get`: {"estado", "cuerpo", "error"}. `chat`: {"estado", "texto", "error"}.
`estado` es el código HTTP, o null si no hubo respuesta.
La llave sale de API_SERVER_KEY o, si falta, de spike/.env; nunca se imprime ni va como argumento.
Si falta la llave sale con código 2 ("no se pudo ejecutar"), que no se confunde con un "falla" (1).
Dirección: HERMES_URL (por defecto http://127.0.0.1:8642).
"""
import argparse
import functools
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TIMEOUT_S = 180


@functools.cache
def leer_llave():
    llave = os.environ.get("API_SERVER_KEY", "")
    entorno = AQUI.parent / ".env"
    if not llave and entorno.exists():
        for linea in entorno.read_text(encoding="utf-8").splitlines():
            linea = linea.removeprefix("export ")
            if linea.startswith("API_SERVER_KEY="):
                # Docker Compose acepta comillas en el .env; aquí se quitan igual para que ambos lean la misma llave.
                llave = linea.split("=", 1)[1].strip().strip("\"'")
    if not llave:
        print("falta API_SERVER_KEY (variable de entorno o spike/.env)", file=sys.stderr)
        raise SystemExit(2)
    return llave


def base_url():
    return os.environ.get("HERMES_URL", "http://127.0.0.1:8642").rstrip("/")


def pedir(metodo, ruta, cuerpo=None, cabeceras=None):
    """Devuelve (estado, texto_crudo, error). `estado` es None si no hubo respuesta HTTP."""
    req = urllib.request.Request(base_url() + ruta, method=metodo)
    req.add_header("Authorization", f"Bearer {leer_llave()}")
    for nombre, valor in (cabeceras or {}).items():
        req.add_header(nombre, valor)
    if cuerpo is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(cuerpo).encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return r.status, r.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return None, "", f"{type(e).__name__}: {e}"


def chat(sesion, texto, sistema=None, modelo="hermes-agent"):
    mensajes = []
    if sistema:
        mensajes.append({"role": "system", "content": sistema})
    mensajes.append({"role": "user", "content": texto})
    estado, crudo, error = pedir(
        "POST", "/v1/chat/completions",
        {"model": modelo, "stream": False, "messages": mensajes},
        {"X-Hermes-Session-Id": sesion})
    salida = {"estado": estado, "texto": None, "error": error}
    if estado == 200:
        try:
            salida["texto"] = json.loads(crudo)["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            salida["error"] = "respuesta sin choices[0].message.content: " + crudo[:200]
    elif estado is not None:
        salida["error"] = f"HTTP {estado}: {crudo[:200]}"
    return salida


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="orden", required=True)
    g = sub.add_parser("get")
    g.add_argument("ruta")
    c = sub.add_parser("chat")
    c.add_argument("--sesion", required=True)
    c.add_argument("--texto", required=True)
    c.add_argument("--sistema", help="archivo con el mensaje de sistema")
    a = ap.parse_args()
    if a.orden == "get":
        estado, crudo, error = pedir("GET", a.ruta)
        try:
            cuerpo = json.loads(crudo) if crudo else None
        except json.JSONDecodeError:
            cuerpo = crudo[:300]
        print(json.dumps({"estado": estado, "cuerpo": cuerpo, "error": error}, ensure_ascii=False))
    else:
        sistema = Path(a.sistema).read_text(encoding="utf-8").strip() if a.sistema else None
        print(json.dumps(chat(a.sesion, a.texto, sistema), ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
