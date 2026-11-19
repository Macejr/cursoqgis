import json
import math
import os
import re

INPUT_FILE = "ComunidadesAutonomas_2.js"
OUTPUT_FILE = "ComunidadesAutonomas_2_reducido.js"

# Ajusta estos dos parámetros según cuánto quieras reducir el tamaño:
DECIMALES = 5  # 5 decimales ≈ 1 metro de precisión (de 15 decimales baja muchísimo el peso)
TOLERANCIA = 0.005  # Grados (~500m). Sube a 0.01 si sigue pesando > 25 MB, baja a 0.001 para más detalle


def perpendicular_distance(pt, line_start, line_end):
    x, y = pt[0], pt[1]
    x1, y1 = line_start[0], line_start[1]
    x2, y2 = line_end[0], line_end[1]
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def douglas_peucker(points, tolerance):
    if len(points) <= 4:  # Mantener polígonos mínimos válidos
        return points
    dmax = 0.0
    index = 0
    for i in range(1, len(points) - 1):
        d = perpendicular_distance(points[i], points[0], points[-1])
        if d > dmax:
            index = i
            dmax = d
    if dmax > tolerance:
        res1 = douglas_peucker(points[: index + 1], tolerance)
        res2 = douglas_peucker(points[index:], tolerance)
        return res1[:-1] + res2
    else:
        return [points[0], points[-1]]


def process_coords(coords):
    # Si es un anillo de coordenadas [[lon, lat], ...]
    if isinstance(coords[0], list) and isinstance(coords[0][0], (int, float)):
        is_closed = coords[0] == coords[-1]
        simplified = douglas_peucker(coords, TOLERANCIA)
        # Asegurar que un polígono cerrado tenga al menos 4 puntos (3 distintos + cierre)
        if is_closed and len(simplified) < 4:
            simplified = coords[:4]
        return [[round(c[0], DECIMALES), round(c[1], DECIMALES)] for c in simplified]
    return [process_coords(sub) for sub in coords]


# 1. Leer el archivo JS original
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    content = f.read().strip()

# Separar la declaración JS (ej. "var json_ComunidadesAutonomas_2 = ") del objeto JSON
match = re.match(r"^(var\s+\w+\s*=\s*)(\{.*\})\s*;?\s*$", content, re.DOTALL)
if not match:
    raise ValueError("No se reconoció el formato 'var nombre = {...};'")

prefix, json_str = match.group(1), match.group(2)
data = json.loads(json_str)

# 2. Simplificar geometrías
for feature in data.get("features", []):
    geom = feature.get("geometry")
    if geom and "coordinates" in geom:
        geom["coordinates"] = process_coords(geom["coordinates"])

# 3. Guardar minificado y manteniendo el formato .js
output_js = (
    prefix + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";"
)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(output_js)

orig_mb = os.path.getsize(INPUT_FILE) / (1024 * 1024)
new_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
print(f"Listo: {orig_mb:.2f} MB -> {new_mb:.2f} MB")