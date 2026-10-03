#!/usr/bin/env python3
"""Bucle de referencia mínimo (T016, SPEC-001). Solo biblioteca estándar. DESCARTABLE.

Sirve para una sola cosa: medir cuántos tokens y cuánto tiempo gasta un bucle propio, con el
mismo modelo, las mismas herramientas MCP, el mismo prompt (bench/prompt_sistema.txt) y el
mismo banco que Hermes, y así calcular la razón de tokens (FR-014, pasa si Hermes ≤ 2×).
NO es el plan B terminado.

Variables de entorno:
  OPENROUTER_API_KEY, OPENROUTER_MODEL      obligatorias
  OPENROUTER_URL   por defecto https://openrouter.ai/api/v1
  MCP_URL          por defecto http://127.0.0.1:5000/mcp (MCP Toolbox, transporte HTTP)

Ejemplo:
  python bucle.py --salida ../bench/salida/baseline.json

Estado: probado solo contra servidores simulados. Falta probarlo con el Toolbox y OpenRouter
reales (T029 y T017); si el Toolbox exige otra versión del protocolo MCP, se ajusta aquí.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BENCH = AQUI.parent / "bench"
sys.path.insert(0, str(BENCH))
import runner  # noqa: E402

MAX_VUELTAS = 5
VERSION_MCP = "2025-03-26"


class ClienteMCP:
    """Cliente MCP mínimo: JSON-RPC por POST, respuesta JSON o SSE, sesión opcional."""

    def __init__(self, url):
        self.url = url
        self.sesion = None
        self._id = 0

    def _post(self, mensaje):
        req = urllib.request.Request(self.url, data=json.dumps(mensaje).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        if self.sesion:
            req.add_header("Mcp-Session-Id", self.sesion)
        with urllib.request.urlopen(req, timeout=60) as r:
            sid = r.headers.get("Mcp-Session-Id")
            if sid:
                self.sesion = sid
            tipo = r.headers.get("Content-Type", "")
            cuerpo = r.read().decode("utf-8")
        if not cuerpo.strip():
            return None
        if "text/event-stream" in tipo:
            for linea in cuerpo.splitlines():
                if linea.startswith("data:"):
                    return json.loads(linea[5:].strip())
            return None
        return json.loads(cuerpo)

    def _llamar(self, metodo, params=None):
        self._id += 1
        resp = self._post({"jsonrpc": "2.0", "id": self._id, "method": metodo, "params": params or {}})
        if resp is None or "error" in resp:
            raise RuntimeError(f"MCP {metodo}: {resp and resp.get('error')}")
        return resp["result"]

    def iniciar(self):
        self._llamar("initialize", {"protocolVersion": VERSION_MCP, "capabilities": {},
                                    "clientInfo": {"name": "bucle-referencia", "version": "0"}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def herramientas(self):
        return self._llamar("tools/list")["tools"]

    def llamar(self, nombre, argumentos):
        r = self._llamar("tools/call", {"name": nombre, "arguments": argumentos})
        texto = "\n".join(p.get("text", "") for p in r.get("content", []) if p.get("type") == "text")
        return texto, bool(r.get("isError"))


def a_formato_openai(herramientas_mcp):
    return [{"type": "function",
             "function": {"name": h["name"], "description": h.get("description", ""),
                          "parameters": h.get("inputSchema", {"type": "object", "properties": {}})}}
            for h in herramientas_mcp]


def crear_responder(cfg):
    mcp = ClienteMCP(cfg["mcp_url"])
    mcp.iniciar()
    herramientas = a_formato_openai(mcp.herramientas())
    prompt = (BENCH / "prompt_sistema.txt").read_text(encoding="utf-8").strip()
    endpoint = cfg["url"].rstrip("/") + "/chat/completions"

    def responder(texto, sesion):
        mensajes = [{"role": "system", "content": prompt}, {"role": "user", "content": texto}]
        salida = {"respuesta": None, "prompt_tokens": 0, "completion_tokens": 0,
                  "tiempo_modelo_s": 0.0, "vueltas": 0, "eventos_429": [], "error": None}
        for _ in range(MAX_VUELTAS):
            r = runner.post_chat(endpoint, {"model": cfg["modelo"], "messages": mensajes,
                                            "tools": herramientas, "stream": False},
                                 cfg["llave"], {}, cfg["reintentos"], cfg["espera_inicial"],
                                 "proveedor-directo")
            salida["eventos_429"] += r["eventos_429"]
            if r["error"]:
                salida["error"] = r["error"]
                return salida
            salida["vueltas"] += 1
            salida["tiempo_modelo_s"] += r["tiempo_s"]
            uso = r["datos"].get("usage") or {}
            salida["prompt_tokens"] += uso.get("prompt_tokens", 0)
            salida["completion_tokens"] += uso.get("completion_tokens", 0)
            try:
                msg = r["datos"]["choices"][0]["message"]
            except (KeyError, IndexError, TypeError):
                salida["error"] = "respuesta sin choices[0].message"
                return salida
            if not msg.get("tool_calls"):
                salida["respuesta"] = msg.get("content")
                salida["tiempo_modelo_s"] = round(salida["tiempo_modelo_s"], 3)
                return salida
            mensajes.append(msg)
            for tc in msg["tool_calls"]:
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                    contenido, _ = mcp.llamar(tc["function"]["name"], args)
                except (json.JSONDecodeError, RuntimeError, OSError) as e:
                    contenido = f"error al usar la herramienta: {e}"
                mensajes.append({"role": "tool", "tool_call_id": tc["id"], "content": contenido})
        salida["error"] = f"se agotaron las {MAX_VUELTAS} vueltas sin respuesta final"
        return salida

    return responder


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", required=True)
    ap.add_argument("--banco", default=str(BENCH / "banco.json"))
    ap.add_argument("--reintentos", type=int, default=5)
    ap.add_argument("--espera-inicial", type=float, default=2.0)
    ap.add_argument("--pausa", type=float, default=0.0)
    ap.add_argument("--limite", type=int, default=None)
    a = ap.parse_args()

    for var in ("OPENROUTER_API_KEY", "OPENROUTER_MODEL"):
        if not os.environ.get(var):
            raise SystemExit(f"falta la variable de entorno {var} (ver spike/.env.example)")
    cfg = {"llave": os.environ["OPENROUTER_API_KEY"], "modelo": os.environ["OPENROUTER_MODEL"],
           "url": os.environ.get("OPENROUTER_URL", "https://openrouter.ai/api/v1"),
           "mcp_url": os.environ.get("MCP_URL", "http://127.0.0.1:5000/mcp"),
           "reintentos": a.reintentos, "espera_inicial": a.espera_inicial}

    banco = runner.cargar_banco(a.banco)
    resultados = runner.correr(banco, crear_responder(cfg), "baseline", a.pausa, a.limite)
    resumen = runner.guardar(a.salida, "baseline", banco, cfg["modelo"], resultados)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(f"guardado en {a.salida}", file=sys.stderr)


if __name__ == "__main__":
    main()
