from dataclasses import dataclass, field
from typing import Literal

import gpxpy
import gpxpy.gpx

from app.core.filenames import InvalidFilenameError, parse_gpx_filename
from app.core.geometry import cumulative_distances_m, haversine_m

Status = Literal["ok", "avertissement", "erreur"]

SWIM_LENGTH_WARNING_THRESHOLD_M = 1500.0
TRONCON_GAP_WARNING_THRESHOLD_M = 30.0


@dataclass
class TronconImportResult:
    filename: str
    course: int | None
    troncon: int | None
    type: str | None
    points: list[tuple[float, float]]
    length_m: float
    status: Status
    messages: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TrackPoint:
    lat: float
    lon: float
    distance_m: float
    troncon: int
    type: str


@dataclass
class CourseAssemblyResult:
    course: int
    track: list[TrackPoint]
    troncon_results: list[TronconImportResult]
    status: Status = "ok"
    messages: list[str] = field(default_factory=list)


def _read_raw_points(gpx: gpxpy.gpx.GPX) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    if not points:
        for route in gpx.routes:
            for point in route.points:
                points.append((point.latitude, point.longitude))
    return points


def _dedupe_consecutive(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    deduped: list[tuple[float, float]] = []
    for point in points:
        if not deduped or deduped[-1] != point:
            deduped.append(point)
    return deduped


def import_troncon_file(filename: str, gpx_content: str) -> TronconImportResult:
    """Parse et contrôle un fichier GPX correspondant à un tronçon.

    Ne lève jamais d'exception : toute erreur est renvoyée dans le résultat
    (status="erreur") pour permettre l'affichage d'un tableau de contrôle
    complet plutôt qu'un échec silencieux ou un arrêt au premier fichier en erreur.
    """
    try:
        parsed_name = parse_gpx_filename(filename)
    except InvalidFilenameError as exc:
        return TronconImportResult(
            filename=filename,
            course=None,
            troncon=None,
            type=None,
            points=[],
            length_m=0.0,
            status="erreur",
            messages=[str(exc)],
        )

    try:
        gpx = gpxpy.parse(gpx_content)
    except Exception as exc:  # gpxpy peut lever plusieurs types d'exceptions XML
        return TronconImportResult(
            filename=filename,
            course=parsed_name.course,
            troncon=parsed_name.troncon,
            type=parsed_name.type,
            points=[],
            length_m=0.0,
            status="erreur",
            messages=[f"Fichier GPX illisible : {exc}"],
        )

    raw_points = _dedupe_consecutive(_read_raw_points(gpx))
    if not raw_points:
        return TronconImportResult(
            filename=filename,
            course=parsed_name.course,
            troncon=parsed_name.troncon,
            type=parsed_name.type,
            points=[],
            length_m=0.0,
            status="erreur",
            messages=["Tronçon vide : aucun point trouvé dans le fichier GPX."],
        )

    length_m = cumulative_distances_m(raw_points)[-1]

    messages: list[str] = []
    if parsed_name.type == "swim" and length_m > SWIM_LENGTH_WARNING_THRESHOLD_M:
        messages.append(
            f"Tronçon de natation anormalement long ({length_m:.0f} m > "
            f"{SWIM_LENGTH_WARNING_THRESHOLD_M:.0f} m)."
        )

    return TronconImportResult(
        filename=filename,
        course=parsed_name.course,
        troncon=parsed_name.troncon,
        type=parsed_name.type,
        points=raw_points,
        length_m=length_m,
        status="avertissement" if messages else "ok",
        messages=messages,
    )


def assemble_course(
    course: int, troncon_results: list[TronconImportResult]
) -> CourseAssemblyResult:
    """Assemble les tronçons valides d'une course en un tracé continu, trié par numéro.

    Les tronçons en erreur (nom invalide, fichier illisible, tronçon vide) sont
    exclus du tracé mais leurs messages sont reportés dans le résultat.
    """
    course_results = [r for r in troncon_results if r.course == course]
    messages: list[str] = []
    status: Status = "ok"

    def warn(message: str) -> None:
        nonlocal status
        messages.append(message)
        if status == "ok":
            status = "avertissement"

    def error(message: str) -> None:
        nonlocal status
        messages.append(message)
        status = "erreur"

    for result in course_results:
        if result.status == "erreur":
            troncon_label = result.troncon if result.troncon is not None else "?"
            error(f"[tronçon {troncon_label}] {'; '.join(result.messages)}")

    seen_troncons: dict[int, TronconImportResult] = {}
    for result in sorted(
        (r for r in course_results if r.status != "erreur"), key=lambda r: r.troncon or 0
    ):
        assert result.troncon is not None
        if result.troncon in seen_troncons:
            error(f"Numéro de tronçon en double dans la course {course} : {result.troncon}.")
            continue
        seen_troncons[result.troncon] = result

    ordered_numbers = sorted(seen_troncons)
    for expected, actual in zip(range(1, len(ordered_numbers) + 1), ordered_numbers):
        if expected != actual:
            warn(
                f"Numéro de tronçon manquant dans la séquence de la course {course} "
                f"(attendu {expected}, trouvé {actual})."
            )

    track: list[TrackPoint] = []
    course_distance = 0.0
    previous_end: tuple[float, float] | None = None
    for number in ordered_numbers:
        result = seen_troncons[number]
        if previous_end is not None and result.points:
            gap = haversine_m(*previous_end, *result.points[0])
            if gap > TRONCON_GAP_WARNING_THRESHOLD_M:
                warn(
                    f"Écart de {gap:.0f} m entre la fin du tronçon précédent et le début "
                    f"du tronçon {number} (course {course})."
                )

        local_distances = cumulative_distances_m(result.points)
        for (lat, lon), local_dist in zip(result.points, local_distances):
            track.append(
                TrackPoint(
                    lat=lat,
                    lon=lon,
                    distance_m=course_distance + local_dist,
                    troncon=number,
                    type=result.type or "",
                )
            )
        if local_distances:
            course_distance += local_distances[-1]
            previous_end = result.points[-1]

    return CourseAssemblyResult(
        course=course, track=track, troncon_results=course_results, status=status, messages=messages
    )


def parse_gpx_points(gpx_content: str) -> list[tuple[float, float]]:
    """Parse un GPX complet (pas encore découpé en tronçons) et renvoie ses points (lat, lon),
    dédupliqués comme pour un tronçon classique. Lève une exception gpxpy si le XML est
    invalide, à charge de l'appelant (voir la route de découpage, `core/gpx_import.py`
    décision dans CLAUDE.md)."""
    gpx = gpxpy.parse(gpx_content)
    return _dedupe_consecutive(_read_raw_points(gpx))


def split_points_at_distances(
    points: list[tuple[float, float]], cut_distances_m: list[float]
) -> list[list[tuple[float, float]]]:
    """Découpe un tracé continu en segments contigus, à des distances cumulées croissantes
    données (en mètres depuis le premier point).

    Insère à chaque coupure un point interpolé exact, partagé entre la fin d'un segment et le
    début du suivant : les segments résultants s'enchaînent donc sans écart (comme des tronçons
    normalement issus de fichiers GPX distincts mais dont la fin/le début coïncident). C'est la
    base de l'écran de découpage manuel d'un unique GPX complet en tronçons Run/Swim (voir la
    décision dans CLAUDE.md : approche purement manuelle, pas de détection automatique).
    """
    if len(points) < 2:
        raise ValueError("Le tracé doit contenir au moins 2 points pour être découpé.")
    if not cut_distances_m:
        return [list(points)]

    distances = cumulative_distances_m(points)
    total = distances[-1]

    sorted_cuts = sorted(cut_distances_m)
    if len(set(sorted_cuts)) != len(sorted_cuts):
        raise ValueError("Deux points de coupure ne peuvent pas être à la même distance.")
    for cut in sorted_cuts:
        if not (0 < cut < total):
            raise ValueError(
                f"Point de coupure à {cut:.0f} m hors du tracé (longueur totale {total:.0f} m)."
            )

    segments: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = [points[0]]
    idx = 0
    for cut in sorted_cuts:
        while idx < len(points) - 2 and distances[idx + 1] < cut:
            idx += 1
            current.append(points[idx])
        lat1, lon1 = points[idx]
        lat2, lon2 = points[idx + 1]
        d1, d2 = distances[idx], distances[idx + 1]
        ratio = 0.0 if d2 == d1 else (cut - d1) / (d2 - d1)
        cut_point = (lat1 + (lat2 - lat1) * ratio, lon1 + (lon2 - lon1) * ratio)
        current.append(cut_point)
        segments.append(current)
        current = [cut_point]
    while idx < len(points) - 1:
        idx += 1
        current.append(points[idx])
    segments.append(current)
    return segments


def points_to_gpx(points: list[tuple[float, float]]) -> str:
    """Sérialise des points (lat, lon) en GPX minimal, pour réécrire les segments issus de
    split_points_at_distances comme des fichiers de tronçon normaux (réutilisés tels quels par
    le pipeline d'import existant — voir la route de découpage)."""
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)
    for lat, lon in points:
        segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    return gpx.to_xml()
