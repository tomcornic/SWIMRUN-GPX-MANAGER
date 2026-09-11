"""Génère un jeu de GPX synthétiques autour de Saint-Pabu (voir §8 du cahier des
charges) : 3 courses, alternance Run/Swim, dont un aller-retour (Course 2, tronçon 3)."""

import math
from pathlib import Path

import gpxpy.gpx

REF_LAT = 48.565
REF_LON = -4.596
EARTH_RADIUS_M = 6371000.0

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def _offset_point(dx_m: float, dy_m: float) -> tuple[float, float]:
    lat = REF_LAT + math.degrees(dy_m / EARTH_RADIUS_M)
    lon = REF_LON + math.degrees(dx_m / (EARTH_RADIUS_M * math.cos(math.radians(REF_LAT))))
    return (lat, lon)


def _line(
    start: tuple[float, float], end: tuple[float, float], n: int, wobble_m: float = 0.0
) -> list[tuple[float, float]]:
    """Points entre deux offsets locaux (mètres), avec une légère ondulation
    perpendiculaire pour un rendu moins robotique qu'une ligne parfaitement droite."""
    x0, y0 = start
    x1, y1 = end
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    nx, ny = (-dy / length, dx / length) if length else (0.0, 0.0)
    points = []
    for i in range(n + 1):
        t = i / n
        wobble = math.sin(t * math.pi * 3) * wobble_m
        points.append(_offset_point(x0 + dx * t + nx * wobble, y0 + dy * t + ny * wobble))
    return points


def _write_gpx(points: list[tuple[float, float]], filename: str) -> None:
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)
    for lat, lon in points:
        segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    (OUTPUT_DIR / filename).write_text(gpx.to_xml())


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Course 1 (XS) : petite boucle littorale, 2 tronçons.
    _write_gpx(_line((0, 0), (600, 150), 80, wobble_m=8), "Course1_Tronçon1_Run.gpx")
    _write_gpx(_line((600, 150), (750, 350), 40, wobble_m=3), "Course1_Tronçon2_Swim.gpx")

    # Course 2 (S) : 4 tronçons, dont un aller-retour sur une pointe rocheuse (tronçon 3).
    _write_gpx(_line((0, 0), (900, 300), 100, wobble_m=10), "Course2_Tronçon1_Run.gpx")
    _write_gpx(_line((900, 300), (1050, 500), 50, wobble_m=4), "Course2_Tronçon2_Swim.gpx")
    out_and_back = _line((1050, 500), (1450, 650), 60, wobble_m=6)
    out_and_back += list(reversed(out_and_back[:-1]))
    _write_gpx(out_and_back, "Course2_Tronçon3_Run.gpx")
    _write_gpx(_line((1050, 500), (1000, 750), 45, wobble_m=4), "Course2_Tronçon4_Swim.gpx")

    # Course 3 (S, variante) : 3 tronçons Run/Swim/Run.
    _write_gpx(_line((0, 0), (700, -200), 90, wobble_m=9), "Course3_Tronçon1_Run.gpx")
    _write_gpx(_line((700, -200), (850, -50), 45, wobble_m=4), "Course3_Tronçon2_Swim.gpx")
    _write_gpx(_line((850, -50), (1400, -300), 100, wobble_m=10), "Course3_Tronçon3_Run.gpx")

    print(f"GPX de démo écrits dans {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
