#!/usr/bin/env python3
"""Verifica los proveedores gratuitos de respaldo (ADR-011). Solo biblioteca estándar.

Corre en tu PC con las llaves de spike/.env (las que falten se saltan). Hace llamadas directas a cada
proveedor y no pasa por Hermes. Las llaves nunca se imprimen.

  verificar_proveedores.py listar [--proveedor groq] [--filtro texto] [--max 60]
      Pide /models y muestra los identificadores de modelo (sin gastar cuota de generación).
      Con --filtro solo los que contienen el texto; sin él, muestra los primeros --max.
  verificar_proveedores.py probar --proveedor groq --modelo <id>
      Una solicitud con una herramienta definida: comprueba que la llave sirve, que el modelo llama a la
      herramienta y muestra las cabeceras de límite (x-ratelimit-*) que devuelva el proveedor.
      Gasta 1 solicitud de la cuota diaria de ese proveedor.

Los puntos de conexión se pueden sustituir con <PROVEEDOR>_BASE_URL (para pruebas con un servidor simulado).
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / ".env"

# nombre -> (url base compatible con OpenAI, variable de entorno de la llave, nombre en Hermes)
PROVEEDORES = {
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "openrouter"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GOOGLE_API_KEY", "gemini"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "custom"),
    "mistral": ("https://api.mistral.ai/v1", "MISTRAL_API_KEY", "custom"),
    "github": ("https://models.github.ai/inference", "GITHUB_MODELS_TOKEN", "custom"),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY", "nvidia"),
}

HERRAMIENTA = {"type": "function", "function": {
    "name": "catalogo_buscar",
    "description": "Busca productos por nombre o categoría y devuelve código, nombre y precio.",
    "parameters": {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"]}}}


def cargar_env():
    valores = dict(os.environ)
    if ENV.exists():
        for linea in ENV.read_text(encoding="utf-8").splitlines():
            linea = linea.removeprefix("export ")
            if "=" in linea and not linea.startswith("#"):
                k, v = linea.split("=", 1)
                valores.setdefault(k.strip(), v.strip().strip("\"'"))
    return valores


def pedir(url, llave, cuerpo=None):
    req = urllib.request.Request(url, method="POST" if cuerpo is not None else "GET")
    req.add_header("Authorization", f"Bearer {llave}")
    req.add_header("User-Agent", "spike-verificar-proveedores")
    if cuerpo is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(cuerpo).encode("utf-8")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace"), time.monotonic() - t0
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace"), time.monotonic() - t0
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return None, {}, f"{type(e).__name__}: {e}", time.monotonic() - t0


def configurado(nombre, env):
    base, var, _ = PROVEEDORES[nombre]
    base = env.get(f"{nombre.upper()}_BASE_URL", base).rstrip("/")
    llave = env.get(var, "")
    if nombre == "gemini" and not llave:
        llave = env.get("GEMINI_API_KEY", "")
    return base, var, llave


def listar(nombres, env, filtro="", maximo=60):
    for n in nombres:
        base, var, llave = configurado(n, env)
        if not llave:
            print(f"[{n}] sin llave ({var} vacía): se salta")
            continue
        estado, _, cuerpo, _ = pedir(f"{base}/models", llave)
        if estado != 200:
            print(f"[{n}] HTTP {estado}: {cuerpo[:160].replace(llave, '<llave>')}")
            continue
        j = json.loads(cuerpo)
        datos = j.get("data", j.get("models", j)) if isinstance(j, dict) else j
        ids = sorted(str(m.get("id", m.get("name", ""))) if isinstance(m, dict) else str(m) for m in datos)
        elegidos = [i for i in ids if filtro.lower() in i.lower()]
        print(f"[{n}] {len(ids)} modelos; coinciden {len(elegidos)}:")
        for i in elegidos[:maximo]:
            print("   ", i)
        if len(elegidos) > maximo:
            print(f"    ... y {len(elegidos) - maximo} más (usa --filtro para acotar)")


def probar(nombre, modelo, env):
    base, var, llave = configurado(nombre, env)
    if not llave:
        print(f"[{nombre}] sin llave ({var} vacía)")
        return 2
    cuerpo = {"model": modelo, "stream": False, "tool_choice": "auto", "tools": [HERRAMIENTA],
              "messages": [{"role": "user", "content": "¿Cuánto cuesta una polera? Usa la herramienta."}]}
    estado, cab, texto, seg = pedir(f"{base}/chat/completions", llave, cuerpo)
    print(f"[{nombre}] {modelo}: HTTP {estado} en {seg:.1f}s")
    limites = {k: v for k, v in cab.items() if any(s in k.lower() for s in ("ratelimit", "retry-after", "quota"))}
    for k, v in sorted(limites.items()):
        print(f"    {k}: {v}")
    if estado != 200:
        print("   ", texto[:300].replace(llave, "<llave>"))
        return 1
    try:
        mensaje = json.loads(texto)["choices"][0]["message"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        print("    respuesta sin choices[0].message")
        return 1
    llamadas = mensaje.get("tool_calls") or []
    print(f"    llamadas a herramientas: {len(llamadas)}" + (f" -> {llamadas[0]['function']['name']}" if llamadas else ""))
    print("    veredicto:", "pasa (llama a la herramienta)" if llamadas else "no concluyente (respondió sin usar la herramienta)")
    return 0 if llamadas else 3


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="orden", required=True)
    a = sub.add_parser("listar")
    a.add_argument("--proveedor", choices=list(PROVEEDORES))
    a.add_argument("--filtro", default="")
    a.add_argument("--max", type=int, default=60)
    b = sub.add_parser("probar")
    b.add_argument("--proveedor", required=True, choices=list(PROVEEDORES))
    b.add_argument("--modelo", required=True)
    args = ap.parse_args()
    env = cargar_env()
    if args.orden == "listar":
        listar([args.proveedor] if args.proveedor else list(PROVEEDORES), env, args.filtro, args.max)
        return 0
    return probar(args.proveedor, args.modelo, env)


if __name__ == "__main__":
    sys.exit(main())
