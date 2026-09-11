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


def project_point_onto_track(
    point: tuple[float, float], track: list[tuple[float, float, float]]
) -> float:
    """Projette `point` (lat, lon) sur le tracé (lat, lon, distance_cumulee_m) et renvoie
    la distance cumulée du point le plus proche sur le tracé (§5 : km des POI).

    Pour chaque segment, on projette orthogonalement dans le plan local équirectangulaire,
    en clampant aux extrémités du segment, puis on garde le segment donnant la plus petite
    distance perpendiculaire.
    """
    if not track:
        raise ValueError("Le tracé est vide.")
    if len(track) == 1:
        return track[0][2]

    ref_lat, ref_lon = track[0][0], track[0][1]
    point_xy = project_equirectangular([point], ref_lat, ref_lon)[0]
    track_xy = project_equirectangular([(lat, lon) for lat, lon, _ in track], ref_lat, ref_lon)

    meilleure_distance = math.inf
    meilleure_distance_cumulee = track[0][2]

    for i in range(len(track) - 1):
        x1, y1 = track_xy[i]
        x2, y2 = track_xy[i + 1]
        d1, d2 = track[i][2], track[i + 1][2]

        dx, dy = x2 - x1, y2 - y1
        longueur_segment_sq = dx * dx + dy * dy
        if longueur_segment_sq == 0:
            t = 0.0
        else:
            t = ((point_xy[0] - x1) * dx + (point_xy[1] - y1) * dy) / longueur_segment_sq
            t = max(0.0, min(1.0, t))

        proj_x, proj_y = x1 + t * dx, y1 + t * dy
        distance = math.hypot(point_xy[0] - proj_x, point_xy[1] - proj_y)

        if distance < meilleure_distance:
            meilleure_distance = distance
            meilleure_distance_cumulee = d1 + t * (d2 - d1)

    return meilleure_distance_cumulee
