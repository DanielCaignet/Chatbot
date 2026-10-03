#!/usr/bin/env python3
"""T031 (SPEC-001, FR-019, R7): no existe vía de SQL libre y una escritura con el rol `lector` falla.

Corre en la VM con Toolbox y Postgres arriba. Cuatro grupos de comprobaciones:
  E  estático: tools.yaml (solo herramientas `postgres-sql` con SELECT fijo) y compose.yml (sin
     `--prebuilt`, sin interfaz, solo la clave del lector, Postgres sin puerto publicado).
  M  por MCP: tools/list devuelve solo las 3 herramientas y no existen las de SQL libre habituales.
  L  en Postgres con el rol `lector`: SELECT funciona (control) y INSERT, UPDATE, DELETE, TRUNCATE,
     DROP, CREATE y leer pg_shadow fallan.
  C  control con el rol `escritor`, dentro de una transacción que se revierte: la escritura SÍ está
     permitida por el esquema, así que el fallo del lector se debe a su rol y no a un esquema roto.
Las contraseñas se leen dentro del contenedor (variables POSTGRES_PASSWORD_*); no pasan por la VM.

Uso:  python3 solo_lectura.py
Salida: salida/solo-lectura-<fecha>.json. Código de salida: 0 pasa, 1 falla, 2 no se pudo ejecutar, 3 no concluyente.
"""
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
URL = "http://127.0.0.1:5000/mcp"
ESPERADAS = {"catalogo_buscar", "item_obtener", "disponibilidad"}
LIBRES = ["execute_sql", "postgres_execute_sql", "postgres-execute-sql", "list_tables", "postgres_list_tables", "query", "sql"]


def rpc(metodo, params=None):
    cuerpo = {"jsonrpc": "2.0", "id": 1, "method": metodo}
    if params is not None:
        cuerpo["params"] = params
    req = urllib.request.Request(URL, data=json.dumps(cuerpo).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8", "replace"))
        except json.JSONDecodeError:
            return {"error": {"message": f"HTTP {e.code}"}}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        return {"fallo_red": f"{type(e).__name__}: {e}"}


def psql(rol, sql):
    """Ejecuta SQL como `rol` dentro del contenedor; devuelve (código, salida combinada)."""
    var = f"POSTGRES_PASSWORD_{rol.upper()}"
    orden = (f'PGPASSWORD="${var}" psql -h 127.0.0.1 -U {rol} -d tienda -v ON_ERROR_STOP=1 -tA -f -')
    r = subprocess.run(["docker", "exec", "-i", "postgres-spike", "sh", "-c", orden],
                       input=sql, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def estatico():
    fallos = []
    texto = (AQUI / "tools.yaml").read_text(encoding="utf-8")
    docs = [d for d in re.split(r"\n---\n", texto) if d.strip() and not d.strip().startswith("#") or "{" in d]
    elementos = []
    for d in docs:
        cuerpo = "\n".join(l for l in d.splitlines() if not l.startswith("#")).strip()
        if cuerpo:
            elementos.append(json.loads(cuerpo))
    herramientas = [e for e in elementos if e.get("kind") == "tool"]
    fuentes = [e for e in elementos if e.get("kind") == "source"]
    if {h["name"] for h in herramientas} != ESPERADAS:
        fallos.append(f"herramientas en tools.yaml: {sorted(h['name'] for h in herramientas)}")
    for h in herramientas:
        sentencia = h.get("statement", "")
        if h.get("type") != "postgres-sql":
            fallos.append(f"{h['name']}: tipo {h.get('type')} (solo se admite postgres-sql)")
        if not re.match(r"(?is)^\s*SELECT\b", sentencia) or ";" in sentencia:
            fallos.append(f"{h['name']}: la sentencia no es un SELECT único")
        n = len(h.get("parameters", []))
        usados = set(re.findall(r"\$(\d+)", sentencia))
        if usados != {str(i) for i in range(1, n + 1)}:
            fallos.append(f"{h['name']}: parámetros {n} no coinciden con los $n de la sentencia {sorted(usados)}")
        if "${" in sentencia or "||" in re.sub(r"'%'\s*\|\|\s*\$\d\s*\|\|\s*'%'", "", sentencia):
            fallos.append(f"{h['name']}: concatenación o plantilla en la sentencia")
    if [f.get("user") for f in fuentes] != ["lector"]:
        fallos.append(f"el source no usa solo el rol lector: {[f.get('user') for f in fuentes]}")
    # Se comprueban solo las líneas reales: los comentarios del archivo mencionan `--prebuilt` para advertirlo.
    compose = "\n".join(re.sub(r"(^|\s)#.*$", "", l) for l in
                        (AQUI / "compose.yml").read_text(encoding="utf-8").splitlines())
    for prohibido in ("--prebuilt", "--ui", "execute-sql"):
        if prohibido in compose:
            fallos.append(f"compose.yml contiene {prohibido}")
    toolbox = compose.split("  toolbox:")[1].split("\nvolumes:")[0]
    claves = re.findall(r"^\s+POSTGRES_PASSWORD_(\w+):", toolbox, re.M)
    if claves != ["LECTOR"]:
        fallos.append(f"la Toolbox recibe contraseñas de: {claves}")
    postgres = compose.split("  postgres:")[1].split("  toolbox:")[0]
    if re.search(r"^\s+ports:", postgres, re.M):
        fallos.append("Postgres publica puertos")
    return fallos


def por_mcp():
    fallos, notas = [], []
    r = rpc("tools/list")
    if "fallo_red" in r:
        return None, [r["fallo_red"]]
    nombres = {t["name"] for t in r.get("result", {}).get("tools", [])}
    if nombres != ESPERADAS:
        fallos.append(f"tools/list devuelve {sorted(nombres)}")
    for libre in LIBRES:
        resp = rpc("tools/call", {"name": libre, "arguments": {"sql": "SELECT 1", "query": "SELECT 1"}})
        res = resp.get("result")
        if "error" not in resp and not (isinstance(res, dict) and res.get("isError")):
            fallos.append(f"la herramienta de SQL libre '{libre}' respondió sin error")
        else:
            notas.append(f"{libre}: rechazada")
    return fallos, notas


def en_postgres():
    fallos, notas = [], []
    codigo, salida = psql("lector", "SELECT count(*) FROM producto;")
    if codigo != 0 or salida != "8":
        return None, [f"control SELECT con lector: código {codigo}, salida {salida[:120]!r}"]
    notas.append("SELECT con lector: ok (8 filas)")
    escrituras = {
        "INSERT": "INSERT INTO producto (id, sku, nombre, categoria, precio, activo) VALUES (99, 'X-1', 'x', 'x', 1, true);",
        "UPDATE": "UPDATE producto SET precio = 1 WHERE id = 1;",
        "DELETE": "DELETE FROM inventario WHERE producto_id = 1;",
        "TRUNCATE": "TRUNCATE inventario;",
        "DROP": "DROP TABLE producto;",
        "CREATE": "CREATE TABLE intruso (id integer);",
        "pg_shadow": "SELECT usename, passwd FROM pg_shadow;",
    }
    for nombre, sql in escrituras.items():
        codigo, salida = psql("lector", sql)
        denegado = codigo != 0 and re.search(r"permission denied|must be owner", salida, re.I)
        if denegado:
            notas.append(f"{nombre} con lector: denegado")
        else:
            fallos.append(f"{nombre} con lector NO falló (código {codigo}): {salida[:120]!r}")
    codigo, salida = psql("escritor",
                          "BEGIN; INSERT INTO producto (id, sku, nombre, categoria, precio, activo) "
                          "VALUES (99, 'X-1', 'x', 'x', 1, true); ROLLBACK;")
    if codigo != 0:
        return None, [f"control con escritor: la escritura tampoco funciona ({salida[:140]!r})"]
    notas.append("INSERT con escritor (revertido): permitido, el esquema sí deja escribir")
    codigo, salida = psql("lector", "SELECT count(*) FROM producto;")
    if salida != "8":
        fallos.append(f"el conteo de producto cambió a {salida!r}")
    return fallos, notas


def main():
    try:
        e_fallos = estatico()
    except (OSError, KeyError, json.JSONDecodeError, IndexError) as e:
        print("no se pudo leer tools.yaml o compose.yml:", e)
        return 2
    m_fallos, m_notas = por_mcp()
    l_fallos, l_notas = en_postgres()
    grupos = {"E (estático)": (e_fallos, []), "M (MCP)": (m_fallos, m_notas), "L/C (Postgres)": (l_fallos, l_notas)}
    inconcluso = False
    resumen = {}
    for nombre, (fallos, notas) in grupos.items():
        if fallos is None:
            print(f"{nombre}: no concluyente -> {notas}")
            resumen[nombre] = {"estado": "no concluyente", "detalle": notas}
            inconcluso = True
            continue
        estado = "falla" if fallos else "pasa"
        print(f"{nombre}: {estado}")
        for n in notas:
            print("   ", n)
        for f in fallos:
            print("    FALLA:", f)
        resumen[nombre] = {"estado": estado, "fallos": fallos, "notas": notas}
    algun_fallo = any(g.get("fallos") for g in resumen.values())
    veredicto, codigo = ("falla", 1) if algun_fallo else (("no concluyente", 3) if inconcluso else ("pasa", 0))
    salida = AQUI / "salida"
    salida.mkdir(exist_ok=True)
    (salida / f"solo-lectura-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json").write_text(
        json.dumps({"veredicto": veredicto, "grupos": resumen}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("veredicto:", veredicto)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
