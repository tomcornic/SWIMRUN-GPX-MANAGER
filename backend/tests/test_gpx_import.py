from app.core.gpx_import import assemble_course, import_troncon_file

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
