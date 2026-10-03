#!/usr/bin/env python3
"""T030 (SPEC-001, FR-018, R7): entradas hostiles contra las herramientas de la Toolbox. Solo biblioteca estándar.

Corre en la VM con Toolbox y Postgres arriba (compose.yml). Cada ataque llama a una herramienta por MCP
(http://127.0.0.1:5000/mcp) con una entrada hostil y debe cumplir DOS cosas:
  1. No alterar la consulta: la respuesta es un rechazo, o solo filas con las columnas declaradas de esa
     herramienta y ninguna fila para una cadena que no es un producto real.
  2. No dañar nada: al final las tablas siguen con sus filas y ninguna llamada tardó como un `pg_sleep`.
Antes se corre un control con una búsqueda legítima: si el control falla, el resultado no concluye nada.

Uso:  python3 ataques.py
Salida: salida/ataques-<fecha>.json. Código de salida: 0 pasa, 1 falla, 2 no se pudo ejecutar, 3 no concluyente.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
URL = os.environ.get("TOOLBOX_URL", "http://127.0.0.1:5000/mcp")  # otra dirección para probar variantes
COLUMNAS = {  # columnas que cada herramienta declara en su SELECT (tools.yaml)
    "catalogo_buscar": {"sku", "nombre", "categoria", "precio"},
    "item_obtener": {"sku", "nombre", "categoria", "precio"},
    "disponibilidad": {"sku", "nombre", "cantidad"},
}
PATRONES = {  # los mismos patrones allowedValues de tools.yaml (los genera generar_tools.py)
    "texto": r"[A-Za-z0-9áéíóúñÁÉÍÓÚÑ .-]{1,60}",
    "sku": r"[A-Za-z0-9-]{1,32}",
}
LIMITE_S = 3.0  # un pg_sleep(5) inyectado superaría esto


def rpc(metodo, params=None, id_=1):
    cuerpo = {"jsonrpc": "2.0", "id": id_, "method": metodo}
    if params is not None:
        cuerpo["params"] = params
    req = urllib.request.Request(URL, data=json.dumps(cuerpo).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            crudo = r.read().decode("utf-8", "replace")
            estado = r.status
    except urllib.error.HTTPError as e:
        crudo, estado = e.read().decode("utf-8", "replace"), e.code
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"estado": None, "error_red": f"{type(e).__name__}: {e}", "seg": time.monotonic() - t0}
    try:
        cuerpo_resp = json.loads(crudo)
    except json.JSONDecodeError:
        cuerpo_resp = {"crudo": crudo[:200]}
    return {"estado": estado, "cuerpo": cuerpo_resp, "seg": time.monotonic() - t0}


def llamar(herramienta, argumentos):
    return rpc("tools/call", {"name": herramienta, "arguments": argumentos})


def filas(resp):
    """Extrae las filas (diccionarios) de una respuesta MCP; None si no es una respuesta con contenido."""
    cuerpo = resp.get("cuerpo") or {}
    res = cuerpo.get("result")
    if not isinstance(res, dict) or res.get("isError"):
        return None
    salida = []
    for bloque in res.get("content", []):
        try:
            dato = json.loads(bloque.get("text", ""))
        except json.JSONDecodeError:
            return None
        salida.extend(dato if isinstance(dato, list) else [dato])
    return salida


def contar_tablas():
    """Cuenta filas por tabla con el administrador, dentro del contenedor (sin pasar la clave por la VM)."""
    cuentas = {}
    for tabla in ("producto", "inventario"):
        r = subprocess.run(
            ["docker", "exec", "postgres-spike", "psql", "-U", "postgres", "-d", "tienda", "-tAc",
             f"SELECT count(*) FROM {tabla}"], capture_output=True, text=True)
        if r.returncode != 0:
            return None
        cuentas[tabla] = int(r.stdout.strip())
    return cuentas


ATAQUES = [
    # (id, herramienta, argumentos, descripción)
    ("A01", "catalogo_buscar", {"texto": "polera' OR '1'='1"}, "comilla simple y OR siempre verdadero"),
    ("A02", "catalogo_buscar", {"texto": "x'; DROP TABLE producto; --"}, "segunda sentencia con DROP"),
    ("A03", "catalogo_buscar", {"texto": "x' UNION SELECT usename, passwd, 1, 1 FROM pg_shadow --"}, "UNION contra pg_shadow"),
    ("A04", "catalogo_buscar", {"texto": "%"}, "comodín de ILIKE"),
    ("A05", "catalogo_buscar", {"texto": "a" * 200}, "texto de 200 caracteres"),
    ("A06", "catalogo_buscar", {"texto": "polera\x00; SELECT 1"}, "byte nulo"),
    ("A07", "catalogo_buscar", {"texto": 12345}, "número donde se espera texto"),
    ("A08", "catalogo_buscar", {"texto": ["polera"]}, "lista donde se espera texto"),
    ("A09", "catalogo_buscar", {"texto": {"$ne": ""}}, "objeto donde se espera texto"),
    ("A10", "catalogo_buscar", {"texto": None}, "valor nulo"),
    ("A11", "catalogo_buscar", {}, "falta el parámetro"),
    ("A12", "catalogo_buscar", {"texto": "polera", "extra": "1; DROP TABLE inventario"}, "parámetro no declarado"),
    ("A13", "item_obtener", {"sku": "POL-NEG-M' OR '1'='1"}, "OR siempre verdadero en el código"),
    ("A14", "item_obtener", {"sku": "1; SELECT pg_sleep(5)"}, "pg_sleep inyectado"),
    ("A15", "item_obtener", {"sku": "CHA-DIS-01"}, "producto descontinuado: no debe aparecer"),
    ("A16", "item_obtener", {"sku": 8}, "número donde se espera texto"),
    ("A17", "disponibilidad", {"sku": "x' UNION SELECT 1, usename, 1 FROM pg_user --"}, "UNION en disponibilidad"),
    ("A18", "disponibilidad", {"sku": "POL-NEG-M); DELETE FROM inventario; --"}, "DELETE tras cerrar paréntesis"),
    ("A19", "disponibilidad", {"sku": "CHA-DIS-01"}, "inventario de un producto descontinuado"),
    ("A20", "disponibilidad", {"sku": "../../etc/passwd"}, "ruta de archivo"),
]


def evaluar(herramienta, argumentos, resp):
    """Devuelve (veredicto, motivo). 'pasa' = rechazo o respuesta sin alterar la consulta."""
    if resp.get("estado") is None:
        return "error", resp["error_red"]
    if resp["seg"] > LIMITE_S:
        return "falla", f"tardó {resp['seg']:.1f}s (¿pg_sleep ejecutado?)"
    datos = filas(resp)
    if datos is None:
        return "pasa", "rechazada o con error (no devolvió filas)"
    permitidas = COLUMNAS[herramienta]
    for fila in datos:
        extra = set(fila) - permitidas
        if extra:
            return "falla", f"columnas fuera de lo declarado: {sorted(extra)}"
    # Solo una entrada válida (el patrón de tools.yaml) puede devolver filas, y nunca de un producto inactivo.
    parametro = "texto" if herramienta == "catalogo_buscar" else "sku"
    valor = argumentos.get(parametro)
    if datos and (not isinstance(valor, str) or not re.fullmatch(PATRONES[parametro], valor)):
        return "falla", f"devolvió {len(datos)} filas para una entrada que no cumple el patrón declarado"
    if datos and any(str(f.get("sku")) == "CHA-DIS-01" for f in datos):
        return "falla", "devolvió un producto descontinuado (activo = false)"
    return "pasa", f"{len(datos)} filas, solo columnas declaradas"


def main():
    ahora = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    antes = contar_tablas()
    if antes is None:
        print("no se pudo contar filas: ¿está postgres-spike levantado y docker accesible?")
        return 2

    control = llamar("catalogo_buscar", {"texto": "polera"})
    f_control = filas(control)
    if control.get("estado") is None:
        print("no se pudo llamar a la Toolbox:", control["error_red"])
        return 2
    control_ok = bool(f_control) and len(f_control) == 2
    print(f"control (búsqueda 'polera'): {len(f_control or [])} filas, esperadas 2 -> {'ok' if control_ok else 'FALLA'}")

    resultados = []
    for id_, herramienta, argumentos, descripcion in ATAQUES:
        resp = llamar(herramienta, argumentos)
        veredicto, motivo = evaluar(herramienta, argumentos, resp)
        resultados.append({"id": id_, "herramienta": herramienta, "descripcion": descripcion,
                           "argumentos": argumentos, "seg": round(resp["seg"], 2),
                           "veredicto": veredicto, "motivo": motivo})
        print(f"  {id_} {herramienta:16} {veredicto:6} {resp['seg']:.2f}s  {descripcion}: {motivo}")

    despues = contar_tablas()
    integra = despues == antes
    print(f"filas antes {antes} / después {despues} -> {'intactas' if integra else 'ALTERADAS'}")

    fallos = [r for r in resultados if r["veredicto"] == "falla"]
    errores = [r for r in resultados if r["veredicto"] == "error"]
    if not control_ok:
        veredicto, codigo = "no concluyente (el control con una búsqueda legítima no devolvió las 2 poleras)", 3
    elif fallos or not integra:
        veredicto, codigo = "falla", 1
    elif errores:
        veredicto, codigo = "no concluyente (hubo ataques sin respuesta)", 3
    else:
        veredicto, codigo = "pasa", 0
    salida = AQUI / "salida"
    salida.mkdir(exist_ok=True)
    (salida / f"ataques-{ahora}.json").write_text(json.dumps(
        {"control_ok": control_ok, "filas_antes": antes, "filas_despues": despues,
         "veredicto": veredicto, "ataques": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("veredicto:", veredicto)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
