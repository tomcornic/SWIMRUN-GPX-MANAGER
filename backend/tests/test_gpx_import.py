import pytest

from app.core.geometry import cumulative_distances_m
from app.core.gpx_import import (
    assemble_course,
    import_troncon_file,
    parse_gpx_points,
    points_to_gpx,
    split_points_at_distances,
)

VALID_TRACK_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="48.5650" lon="-4.5960"></trkpt>
    <trkpt lat="48.5651" lon="-4.5961"></trkpt>
    <trkpt lat="48.5651" lon="-4.5961"></trkpt>
    <trkpt lat="48.5652" lon="-4.5962"></trkpt>
  </trkseg></trk>
</gpx>
"""

ROUTE_ONLY_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <rte>
    <rtept lat="48.5650" lon="-4.5960"></rtept>
    <rtept lat="48.5660" lon="-4.5970"></rtept>
  </rte>
</gpx>
"""

EMPTY_TRACK_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg></trkseg></trk>
</gpx>
"""

MALFORMED_GPX = "<gpx><trk><trkseg><trkpt lat=\"48\""  # XML non fermé


def _swim_gpx_longer_than(meters: float) -> str:
    # ~0.001° de latitude = ~111 m ; on construit assez de points pour dépasser le seuil.
    n_points = int(meters / 100) + 5
    points = "".join(
        f'<trkpt lat="{48.565 + i * 0.001:.6f}" lon="-4.596"></trkpt>\n' for i in range(n_points)
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>{points}</trkseg></trk>
</gpx>
"""


def test_import_valid_run_troncon():
    result = import_troncon_file("Course1_Tronçon1_Run.gpx", VALID_TRACK_GPX)
    assert result.status == "ok"
    assert result.course == 1
    assert result.troncon == 1
    assert result.type == "run"
    assert len(result.points) == 3  # le point dupliqué consécutif est supprimé
    assert result.length_m > 0


def test_import_falls_back_to_route_points():
    result = import_troncon_file("Course1_Tronçon2_Swim.gpx", ROUTE_ONLY_GPX)
    assert result.status == "ok"
    assert len(result.points) == 2


def test_import_invalid_filename_is_error():
    result = import_troncon_file("fichier_bizarre.gpx", VALID_TRACK_GPX)
    assert result.status == "erreur"
    assert result.points == []


def test_import_malformed_xml_is_error():
    result = import_troncon_file("Course1_Tronçon1_Run.gpx", MALFORMED_GPX)
    assert result.status == "erreur"
    assert "illisible" in result.messages[0]


def test_import_empty_troncon_is_error():
    result = import_troncon_file("Course1_Tronçon1_Run.gpx", EMPTY_TRACK_GPX)
    assert result.status == "erreur"
    assert "vide" in result.messages[0]


def test_import_swim_troncon_abnormally_long_is_warning():
    long_gpx = _swim_gpx_longer_than(1600)
    result = import_troncon_file("Course1_Tronçon1_Swim.gpx", long_gpx)
    assert result.status == "avertissement"
    assert "anormalement long" in result.messages[0]


def test_assemble_course_orders_and_concatenates_troncons():
    troncon2 = import_troncon_file("Course1_Tronçon2_Swim.gpx", ROUTE_ONLY_GPX)
    troncon1 = import_troncon_file("Course1_Tronçon1_Run.gpx", VALID_TRACK_GPX)

    result = assemble_course(1, [troncon2, troncon1])

    assert result.status == "ok"
    assert [p.troncon for p in result.track[:3]] == [1, 1, 1]
    assert result.track[0].distance_m == 0.0
    # Le tracé assemblé est croissant en distance cumulée.
    distances = [p.distance_m for p in result.track]
    assert distances == sorted(distances)


def test_assemble_course_detects_duplicate_troncon_number():
    troncon1a = import_troncon_file("Course1_Tronçon1_Run.gpx", VALID_TRACK_GPX)
    troncon1b = import_troncon_file("Course1_Tronçon1_Run.gpx", VALID_TRACK_GPX)

    result = assemble_course(1, [troncon1a, troncon1b])

    assert result.status == "erreur"
    assert any("double" in m for m in result.messages)


def test_assemble_course_warns_on_missing_number_in_sequence():
    troncon1 = import_troncon_file("Course1_Tronçon1_Run.gpx", VALID_TRACK_GPX)
    troncon3 = import_troncon_file("Course1_Tronçon3_Swim.gpx", ROUTE_ONLY_GPX)

    result = assemble_course(1, [troncon1, troncon3])

    assert result.status == "avertissement"
    assert any("manquant" in m for m in result.messages)


def test_assemble_course_warns_on_large_gap_between_troncons():
    # Tronçon 2 démarre très loin de la fin du tronçon 1 (> 30 m).
    far_gpx = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="49.0000" lon="-4.5960"></trkpt>
    <trkpt lat="49.0010" lon="-4.5960"></trkpt>
  </trkseg></trk>
</gpx>
"""
    troncon1 = import_troncon_file("Course1_Tronçon1_Run.gpx", VALID_TRACK_GPX)
    troncon2 = import_troncon_file("Course1_Tronçon2_Swim.gpx", far_gpx)

    result = assemble_course(1, [troncon1, troncon2])

    assert result.status == "avertissement"
    assert any("Écart" in m for m in result.messages)


def test_parse_gpx_points_returns_deduped_points():
    assert parse_gpx_points(VALID_TRACK_GPX) == [
        (48.5650, -4.5960),
        (48.5651, -4.5961),
        (48.5652, -4.5962),
    ]


# Tracé rectiligne de 4 points espacés d'environ 111 m (0,001° de latitude), soit ~333 m au total.
STRAIGHT_LINE = [(48.0 + i * 0.001, -4.5) for i in range(4)]


def test_split_without_cuts_returns_single_segment():
    segments = split_points_at_distances(STRAIGHT_LINE, [])
    assert segments == [STRAIGHT_LINE]


def test_split_at_one_cut_produces_two_contiguous_segments():
    total = cumulative_distances_m(STRAIGHT_LINE)[-1]
    segments = split_points_at_distances(STRAIGHT_LINE, [total / 2])

    assert len(segments) == 2
    # Le point de coupure est partagé : fin du premier segment == début du second.
    assert segments[0][-1] == segments[1][0]
    # Aucun point d'origine perdu au passage (hormis la duplication du point de coupure).
    assert segments[0][0] == STRAIGHT_LINE[0]
    assert segments[1][-1] == STRAIGHT_LINE[-1]

    d0 = cumulative_distances_m(segments[0])[-1]
    d1 = cumulative_distances_m(segments[1])[-1]
    assert d0 == pytest.approx(total / 2, abs=1.0)
    assert d0 + d1 == pytest.approx(total, abs=1.0)


def test_split_at_two_cuts_produces_three_segments_in_order():
    total = cumulative_distances_m(STRAIGHT_LINE)[-1]
    segments = split_points_at_distances(STRAIGHT_LINE, [total * 0.7, total * 0.3])

    assert len(segments) == 3
    assert segments[0][-1] == segments[1][0]
    assert segments[1][-1] == segments[2][0]


def test_split_rejects_cut_outside_track():
    total = cumulative_distances_m(STRAIGHT_LINE)[-1]
    with pytest.raises(ValueError, match="hors du tracé"):
        split_points_at_distances(STRAIGHT_LINE, [total + 10])


def test_split_rejects_duplicate_cut_distance():
    total = cumulative_distances_m(STRAIGHT_LINE)[-1]
    with pytest.raises(ValueError, match="même distance"):
        split_points_at_distances(STRAIGHT_LINE, [total / 2, total / 2])


def test_split_requires_at_least_two_points():
    with pytest.raises(ValueError, match="au moins 2 points"):
        split_points_at_distances([(48.0, -4.5)], [10.0])


def test_points_to_gpx_roundtrips_through_parse_gpx_points():
    xml = points_to_gpx(STRAIGHT_LINE)
    assert parse_gpx_points(xml) == STRAIGHT_LINE
