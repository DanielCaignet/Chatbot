#!/usr/bin/env python3
"""Genera tools.yaml para MCP Toolbox desde esquema.json (T028, SPEC-001, FR-017).

Las herramientas no se escriben a mano: cada una sale de un patrón (buscar, obtener,
existencias) aplicado a las tablas y columnas que declara esquema.json. El SQL resultante es
fijo, con parámetros posicionales ($1…) y tipados; nunca se concatenan valores del usuario.

Formato de salida: documentos YAML separados por `---`, cada uno escrito como JSON
(el JSON es YAML válido). Eso permite verificar la salida con la biblioteca estándar.
Formato de Toolbox: `kind: source` / `kind: tool` con `type:` (mcp-toolbox.dev, 2026-10-03).

Uso:
  python generar_tools.py                     # escribe tools.yaml junto a este archivo
  python generar_tools.py --salida otro.yaml
"""
import argparse
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")
TIPOS_PARAM = {"string", "integer", "float", "boolean"}
# Defensa en profundidad. La protección real es el parámetro posicional $1.
PATRON_TEXTO = "^[A-Za-z0-9áéíóúñÁÉÍÓÚÑ .-]{1,60}$"
PATRON_SKU = "^[A-Za-z0-9-]{1,32}$"


def ident(valor, contexto):
    """Un nombre de tabla o columna solo puede ser minúsculas, números y guion bajo."""
    if not isinstance(valor, str) or not IDENT.match(valor):
        raise SystemExit(f"identificador inválido en {contexto}: {valor!r}")
    return valor


def columna(esquema, tabla, col, contexto):
    ident(col, contexto)
    if col not in esquema["tablas"][tabla]["columnas"]:
        raise SystemExit(f"la columna {col!r} no existe en la tabla {tabla!r} ({contexto})")
    return col


def tabla_de(esquema, nombre, contexto):
    ident(nombre, contexto)
    if nombre not in esquema["tablas"]:
        raise SystemExit(f"la tabla {nombre!r} no existe en el esquema ({contexto})")
    return nombre


def filtro_activo(esquema, tabla, alias=""):
    col = esquema["tablas"][tabla].get("columna_activo")
    if not col:
        return ""
    return f" AND {alias}{columna(esquema, tabla, col, 'columna_activo')}"


def herramienta_buscar(esquema, h):
    t = tabla_de(esquema, h["tabla"], h["nombre"])
    meta = esquema["tablas"][t]
    visibles = ", ".join(columna(esquema, t, c, h["nombre"]) for c in meta["visibles"])
    buscables = [columna(esquema, t, c, h["nombre"]) for c in meta["buscables"]]
    coincide = " OR ".join(f"{c} ILIKE '%' || $1 || '%'" for c in buscables)
    limite = int(h.get("limite", 10))
    sql = f"SELECT {visibles} FROM {t} WHERE ({coincide}){filtro_activo(esquema, t)} ORDER BY {buscables[0]} LIMIT {limite}"
    params = [{"name": "texto", "type": "string",
               "description": "Texto corto a buscar en nombre o categoría.",
               "allowedValues": [PATRON_TEXTO]}]
    return sql, params


def herramienta_obtener(esquema, h):
    t = tabla_de(esquema, h["tabla"], h["nombre"])
    meta = esquema["tablas"][t]
    clave = columna(esquema, t, meta["clave"], h["nombre"])
    visibles = ", ".join(columna(esquema, t, c, h["nombre"]) for c in meta["visibles"])
    sql = f"SELECT {visibles} FROM {t} WHERE {clave} = $1{filtro_activo(esquema, t)}"
    params = [{"name": clave, "type": "string",
               "description": "Código exacto del producto.",
               "allowedValues": [PATRON_SKU]}]
    return sql, params


def herramienta_existencias(esquema, h):
    hijo = tabla_de(esquema, h["tabla"], h["nombre"])
    ref = esquema["tablas"][hijo]["referencia"]
    padre = tabla_de(esquema, ref["tabla"], h["nombre"])
    col_hijo = columna(esquema, hijo, ref["columna"], h["nombre"])
    col_padre = columna(esquema, padre, ref["columna_destino"], h["nombre"])
    clave = columna(esquema, padre, esquema["tablas"][padre]["clave"], h["nombre"])
    sel = [f"p.{columna(esquema, padre, c, h['nombre'])}" for c in h["columnas_padre"]]
    sel += [f"i.{columna(esquema, hijo, c, h['nombre'])}" for c in h["columnas_propias"]]
    sql = (f"SELECT {', '.join(sel)} FROM {hijo} i JOIN {padre} p ON i.{col_hijo} = p.{col_padre} "
           f"WHERE p.{clave} = $1{filtro_activo(esquema, padre, 'p.')}")
    params = [{"name": clave, "type": "string",
               "description": "Código exacto del producto.",
               "allowedValues": [PATRON_SKU]}]
    return sql, params


PATRONES = {"buscar": herramienta_buscar, "obtener": herramienta_obtener,
            "existencias": herramienta_existencias}


def construir(esquema):
    o = esquema["origen"]
    docs = [{"kind": "source", "name": o["nombre"], "type": "postgres",
             "host": o["host"], "port": o["puerto"], "database": o["base"],
             "user": o["usuario"], "password": "${" + o["clave_env"] + "}"}]
    for h in esquema["herramientas"]:
        if h["patron"] not in PATRONES:
            raise SystemExit(f"patrón desconocido en {h['nombre']}: {h['patron']!r}")
        sql, params = PATRONES[h["patron"]](esquema, h)
        docs.append({"kind": "tool", "name": ident(h["nombre"], "nombre de herramienta"),
                     "type": "postgres-sql", "source": o["nombre"],
                     "description": h["descripcion"], "parameters": params, "statement": sql})
    return docs


def validar(docs):
    """Comprobaciones deterministas del resultado (FR-018, FR-019)."""
    errores = []
    for d in docs:
        if d["kind"] != "tool":
            continue
        s, n = d["statement"], d["name"]
        if not s.upper().startswith("SELECT "):
            errores.append(f"{n}: no empieza con SELECT")
        if ";" in s:
            errores.append(f"{n}: contiene ';'")
        usados = {int(x) for x in re.findall(r"\$(\d+)", s)}
        if usados != set(range(1, len(d["parameters"]) + 1)):
            errores.append(f"{n}: los $n del SQL no coinciden con los parámetros ({sorted(usados)})")
        for p in d["parameters"]:
            if p["type"] not in TIPOS_PARAM:
                errores.append(f"{n}: tipo de parámetro inválido {p['type']!r}")
    if errores:
        raise SystemExit("validación fallida:\n  " + "\n  ".join(errores))


def escribir(docs, ruta):
    partes = [json.dumps(d, ensure_ascii=False, indent=2) for d in docs]
    cabecera = ("# GENERADO por spike/toolbox/generar_tools.py desde esquema.json. No editar a mano.\n"
                "# Cada documento es JSON (YAML válido). Contraseña por variable de entorno.\n")
    Path(ruta).write_text(cabecera + "\n---\n".join(partes) + "\n", encoding="utf-8")


def leer(ruta):
    """Vuelve a leer lo escrito (sin comentarios) para comprobar que es válido."""
    texto = "".join(l for l in Path(ruta).read_text(encoding="utf-8").splitlines(True) if not l.startswith("#"))
    return [json.loads(parte) for parte in texto.split("\n---\n") if parte.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--esquema", default=str(AQUI / "esquema.json"))
    ap.add_argument("--salida", default=str(AQUI / "tools.yaml"))
    a = ap.parse_args()
    esquema = json.loads(Path(a.esquema).read_text(encoding="utf-8"))
    docs = construir(esquema)
    validar(docs)
    escribir(docs, a.salida)
    releido = leer(a.salida)
    if releido != docs:
        raise SystemExit("lo escrito no coincide con lo generado")
    print(f"{a.salida}: {sum(d['kind'] == 'tool' for d in docs)} herramientas + 1 origen", file=sys.stderr)


if __name__ == "__main__":
    main()
