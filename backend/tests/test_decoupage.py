import json
from io import BytesIO
from pathlib import Path

from app.core.geometry import cumulative_distances_m
from app.core.gpx_import import parse_gpx_points
from app.models import Course, Troncon

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"
FULL_TRACK_GPX = (DEMO_DIR / "Course1_Tronçon1_Run.gpx").read_bytes()
FULL_TRACK_TOTAL_M = cumulative_distances_m(parse_gpx_points(FULL_TRACK_GPX.decode("utf-8")))[-1]


def _create_event_and_course(client) -> int:
    client.post(
        "/orga/evenement",
        data={"name": "Swimrun de Saint-Pabu", "date": "2027-07-12"},
        follow_redirects=True,
    )
    client.post(
        "/orga/courses/nouvelle",
        data={"name": "Course XS", "color": "#1d4ed8", "start_time": "09:00"},
        follow_redirects=True,
    )
    with client.application.app_context():
        return Course.query.first().id


def _upload_full_track(client, course_id: int):
    return client.post(
        f"/orga/courses/{course_id}/decoupage",
        data={"fichier": (BytesIO(FULL_TRACK_GPX), "tracé_parcours.gpx")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


def test_decoupage_upload_then_tracer_shows_map(logged_in_client):
    course_id = _create_event_and_course(logged_in_client)
    response = _upload_full_track(logged_in_client, course_id)
    assert response.status_code == 200
    assert b"decoupage-map-app" in response.data


def test_decoupage_tracer_without_source_redirects(logged_in_client):
    course_id = _create_event_and_course(logged_in_client)
    response = logged_in_client.get(
        f"/orga/courses/{course_id}/decoupage/tracer", follow_redirects=True
    )
    assert b"Importez d" in response.data


def test_decoupage_source_geojson_returns_linestring(logged_in_client):
    course_id = _create_event_and_course(logged_in_client)
    _upload_full_track(logged_in_client, course_id)

    response = logged_in_client.get(f"/orga/courses/{course_id}/decoupage/source.geojson")
    geojson = response.get_json()
    assert geojson["geometry"]["type"] == "LineString"
    assert len(geojson["geometry"]["coordinates"]) > 50


def test_decoupage_valider_without_cuts_creates_single_troncon(logged_in_client, app):
    course_id = _create_event_and_course(logged_in_client)
    _upload_full_track(logged_in_client, course_id)

    response = logged_in_client.post(
        f"/orga/courses/{course_id}/decoupage/valider",
        data={"decoupage_json": json.dumps({"cuts_m": [], "types": ["swim"]})},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Tron\xc3\xa7on1_Swim" in response.data

    logged_in_client.post(f"/orga/courses/{course_id}/import/valider", follow_redirects=True)
    with app.app_context():
        troncons = Troncon.query.filter_by(course_id=course_id).all()
        assert len(troncons) == 1
        assert troncons[0].type == "swim"


def test_decoupage_valider_with_cuts_creates_contiguous_troncons(logged_in_client, app):
    course_id = _create_event_and_course(logged_in_client)
    _upload_full_track(logged_in_client, course_id)

    cut = FULL_TRACK_TOTAL_M / 2
    response = logged_in_client.post(
        f"/orga/courses/{course_id}/decoupage/valider",
        data={"decoupage_json": json.dumps({"cuts_m": [cut], "types": ["run", "swim"]})},
        follow_redirects=True,
    )
    assert response.status_code == 200
    # Le découpage produit un tracé contigu (le point de coupure est partagé), donc aucun
    # avertissement d'écart entre tronçons ne doit apparaître dans l'aperçu.
    assert b"\xc3\x89cart" not in response.data
    assert b">ok<" in response.data or b"status-ok" in response.data

    validate_response = logged_in_client.post(
        f"/orga/courses/{course_id}/import/valider", follow_redirects=True
    )
    assert validate_response.status_code == 200

    with app.app_context():
        troncons = Troncon.query.filter_by(course_id=course_id).order_by(Troncon.number).all()
        assert [t.number for t in troncons] == [1, 2]
        assert [t.type for t in troncons] == ["run", "swim"]
        # Le tracé est contigu : fin du tronçon 1 == début du tronçon 2.
        assert troncons[0].points[-1] == troncons[1].points[0]


def test_decoupage_valider_rejects_type_count_mismatch(logged_in_client):
    course_id = _create_event_and_course(logged_in_client)
    _upload_full_track(logged_in_client, course_id)

    response = logged_in_client.post(
        f"/orga/courses/{course_id}/decoupage/valider",
        data={"decoupage_json": json.dumps({"cuts_m": [100.0], "types": ["run"]})},
        follow_redirects=True,
    )
    assert b"doit avoir un type" in response.data


def test_decoupage_requires_login(client):
    response = client.get("/orga/courses/1/decoupage", follow_redirects=True)
    assert b"Connexion" in response.data
