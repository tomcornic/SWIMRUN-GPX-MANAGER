import math

EARTH_RADIUS_M = 6371000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def cumulative_distances_m(points: list[tuple[float, float]]) -> list[float]:
    if not points:
        return []
    distances = [0.0]
    for (lat1, lon1), (lat2, lon2) in zip(points, points[1:]):
        distances.append(distances[-1] + haversine_m(lat1, lon1, lat2, lon2))
    return distances


def project_equirectangular(
    points: list[tuple[float, float]], ref_lat: float, ref_lon: float
) -> list[tuple[float, float]]:
    """Projection locale équirectangulaire (x, y en mètres), valable à l'échelle de quelques km."""
    ref_lat_rad = math.radians(ref_lat)
    projected = []
    for lat, lon in points:
        x = math.radians(lon - ref_lon) * math.cos(ref_lat_rad) * EARTH_RADIUS_M
        y = math.radians(lat - ref_lat) * EARTH_RADIUS_M
        projected.append((x, y))
    return projected


def resample_by_distance(
    points: list[tuple[float, float, float]], step_m: float
) -> list[tuple[float, float, float]]:
    """Rééchantillonne un tracé (lat, lon, distance_cumulee_m) tous les step_m mètres.

    points doit être trié par distance croissante. Le premier et le dernier point
    d'origine sont toujours conservés.
    """
    if not points:
        return []

    resampled = [points[0]]
    total = points[-1][2]
    target = step_m
    idx = 0
    while target < total:
        while idx < len(points) - 2 and points[idx + 1][2] < target:
            idx += 1
        lat1, lon1, d1 = points[idx]
        lat2, lon2, d2 = points[idx + 1]
        ratio = 0.0 if d2 == d1 else (target - d1) / (d2 - d1)
        resampled.append((lat1 + (lat2 - lat1) * ratio, lon1 + (lon2 - lon1) * ratio, target))
        target += step_m

    if resampled[-1][2] != points[-1][2]:
        resampled.append(points[-1])
    return resampled
