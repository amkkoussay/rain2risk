"""Combine provider outputs into source-aware cell features."""
def build_features(cells, elevations, worldcover_cells, osm_payload, derive_slope):
    if len(elevations) != len(cells) or len(worldcover_cells) != len(cells):
        raise ValueError("provider output length does not match grid")
    for index, cell in enumerate(cells):
        cell["elevation_m"] = elevations[index]
        cell["elevation_status"] = "available" if elevations[index] is not None else "failed"
        cell.update(worldcover_cells[index])
    slopes = derive_slope(cells, elevations)
    for cell, slope in zip(cells, slopes):
        cell["slope_deg"] = slope
        cell["slope_status"] = "available" if slope is not None else "failed"
    if osm_payload is None:
        for cell in cells:
            cell.update({"waterway_present": None, "building_count": None, "water_distance_m": None, "landuse_tags": None,
                         "osm_status": "failed"})
        return cells
    from .osm import extract_facts
    cells = extract_facts(cells, osm_payload)
    for cell in cells: cell["osm_status"] = "available"
    return cells
