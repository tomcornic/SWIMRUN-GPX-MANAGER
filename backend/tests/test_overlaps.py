import math

from app.core.geometry import cumulative_distances_m
from app.core.overlaps import detect_multiple_passages

REF_LAT, REF_LON = 48.565, -4.596
EARTH_RADIUS_M = 6371000.0


def _offset_point(dx_m: float, dy_m: float) -> tuple[float, float]:
    """Inverse de la projection équirectangulaire : (dx, dy) en mètres -> (lat, lon)."""
    lat = REF_LAT + math.degrees(dy_m / EARTH_RADIUS_M)
    lon = REF_LON + math.degrees(dx_m / (EARTH_RADIUS_M * math.cos(math.radians(REF_LAT))))
    return (lat, lon)


def _track_with_distances(xy_points: list[tuple[float, float]]) -> list[tuple[float, float, float]]:
    latlon = [_offset_point(x, y) for x, y in xy_points]
    distances = cumulative_distances_m(latlon)
    return [(lat, lon, d) for (lat, lon), d in zip(latlon, distances)]


def test_no_overlap_on_a_simple_straight_line():
    xy = [(x, 0.0) for x in range(0, 501, 5)]
    track = _track_with_distances(xy)
    assert detect_multiple_passages(track) == []


def test_detects_out_and_back_as_a_single_group_with_two_passages():
    outbound = [(x, 0.0) for x in range(0, 501, 1)]
    inbound = [(x, 0.0) for x in range(499, -1, -1)]
    track = _track_with_distances(outbound + inbound)

    groups = detect_multiple_passages(track)

    assert len(groups) == 1
    passages = groups[0].passages
    assert len(passages) == 2
    # Les deux passages couvrent l'essentiel de l'aller et du retour (~500 m chacun,
    # tronqués près du demi-tour par la zone d'exclusion min_gap_m).
    for passage in passages:
        assert passage.end_distance_m - passage.start_distance_m >= 350
    # Le premier passage démarre bien au début du tracé, le second se termine à la fin.
    assert passages[0].start_distance_m < 10
    assert passages[1].end_distance_m > track[-1][2] - 10


def test_figure_eight_like_track_detects_two_distinct_spurs():
    """Piste en forme de « 8 » simplifiée : un point central (hub) d'où partent deux
    branches aller-retour distinctes (au lieu de deux boucles arrondies, pour garder
    une géométrie facile à vérifier). Chaque branche doit être détectée comme un
    groupe de superposition séparé, localisé sur sa portion du tracé.
    """
    hub = (0.0, 0.0)
    spur_a_out = [(0.0, y) for y in range(0, 301, 1)]
    spur_a_back = [(0.0, y) for y in range(299, -1, -1)]
    spur_b_out = [(x, 0.0) for x in range(0, 301, 1)]
    spur_b_back = [(x, 0.0) for x in range(299, -1, -1)]

    track = _track_with_distances([hub, *spur_a_out, *spur_a_back, *spur_b_out, *spur_b_back])

    groups = detect_multiple_passages(track)

    assert len(groups) == 2
    for group in groups:
        assert len(group.passages) == 2
        for passage in group.passages:
            assert passage.end_distance_m - passage.start_distance_m >= 150

    # Les deux groupes sont bien localisés sur des portions disjointes du tracé
    # (branche A avant le hub de retour, branche B après).
    end_of_group_0 = max(p.end_distance_m for p in groups[0].passages)
    start_of_group_1 = min(p.start_distance_m for p in groups[1].passages)
    assert end_of_group_0 <= start_of_group_1 + 50
