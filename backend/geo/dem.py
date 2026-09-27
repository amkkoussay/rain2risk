"""Open-Meteo elevation provider and slope derivation."""
import json, math
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .grid import cell_dimensions_m

class DEMError(RuntimeError): pass

def fetch_elevations(cells, requester=urlopen):
    query = urlencode({"latitude": ",".join(str(c["lat"]) for c in cells), "longitude": ",".join(str(c["lon"]) for c in cells)})
    request = Request(f"https://api.open-meteo.com/v1/elevation?{query}", headers={"User-Agent": "Rain2Risk/1.0"})
    try:
        with requester(request, timeout=30) as response: payload = json.loads(response.read().decode())
    except Exception as error: raise DEMError("elevation data is unavailable") from error
    values = payload.get("elevation")
    if not isinstance(values, list) or len(values) != len(cells):
        raise DEMError("elevation data is unavailable")
    if any(v is None for v in values): raise DEMError("elevation data is unavailable")
    return {"values": [float(v) for v in values], "source": "Open-Meteo Elevation / Copernicus DEM", "status": "available"}

def derive_slopes(cells, elevations):
    by_index = {(c["row"], c["col"]): i for i, c in enumerate(cells)}
    max_row, max_col = max(x["row"] for x in cells), max(x["col"] for x in cells)
    slopes = []
    for cell in cells:
        r, c = cell["row"], cell["col"]
        r0, r1 = max(0, r - 1), min(max_row, r + 1)
        c0, c1 = max(0, c - 1), min(max_col, c + 1)
        neighbors = [elevations[by_index[(r0,c)]], elevations[by_index[(r1,c)]],
                     elevations[by_index[(r,c0)]], elevations[by_index[(r,c1)]]]
        if any(v is None for v in neighbors):
            slopes.append(None); continue
        north, south, west, east = neighbors
        dy = cell_dimensions_m(cells[by_index[(r0,c)]])[0] if r0 != r1 else cell_dimensions_m(cell)[0]
        dx = cell_dimensions_m(cells[by_index[(r,c0)]])[1] if c0 != c1 else cell_dimensions_m(cell)[1]
        dz_dy, dz_dx = (south - north) / max(dy,1.0), (east - west) / max(dx,1.0)
        slopes.append(round(math.degrees(math.atan(math.hypot(dz_dx,dz_dy))), 2))
    return slopes
