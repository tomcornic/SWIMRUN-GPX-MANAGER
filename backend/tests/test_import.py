from io import BytesIO
from pathlib import Path

from app.models import Course, Troncon

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


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


def _upload(client, course_id: int, filenames: list[str]):
    files = [(BytesIO((DEMO_DIR / name).read_bytes()), name) for name in filenames]
    return client.post(
        f"/orga/courses/{course_id}/import",
        data={"fichiers": files},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


def test_import_preview_shows_ok_status(logged_in_client, app):
    course_id = _create_event_and_course(logged_in_client)
    response = _upload(
        logged_in_client, course_id, ["Course1_Tronçon1_Run.gpx", "Course1_Tronçon2_Swim.gpx"]
    )
    assert response.status_code == 200
    assert b"ok" in response.data
    assert "Tronçon1_Run".encode() in response.data


def test_import_valider_persists_troncons(logged_in_client, app):
    course_id = _create_event_and_course(logged_in_client)
    _upload(logged_in_client, course_id, ["Course1_Tronçon1_Run.gpx", "Course1_Tronçon2_Swim.gpx"])

    response = logged_in_client.post(
        f"/orga/courses/{course_id}/import/valider", follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        troncons = Troncon.query.filter_by(course_id=course_id).order_by(Troncon.number).all()
        assert [t.number for t in troncons] == [1, 2]
        assert [t.type for t in troncons] == ["run", "swim"]
        assert all(t.length_m > 0 for t in troncons)
        assert len(troncons[0].points) > 0

    geo_response = logged_in_client.get(f"/orga/courses/{course_id}/trace.geojson")
    geojson = geo_response.get_json()
    assert geojson["geometry"]["type"] == "LineString"
    assert len(geojson["geometry"]["coordinates"]) > 0


def test_import_with_invalid_filename_is_rejected(logged_in_client, app, tmp_path):
    course_id = _create_event_and_course(logged_in_client)

    bad_file = tmp_path / "fichier_bizarre.gpx"
    bad_file.write_text((DEMO_DIR / "Course1_Tronçon1_Run.gpx").read_text())

    response = logged_in_client.post(
        f"/orga/courses/{course_id}/import",
        data={"fichiers": [(BytesIO(bad_file.read_bytes()), "fichier_bizarre.gpx")]},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"erreur" in response.data

    validate_response = logged_in_client.post(
        f"/orga/courses/{course_id}/import/valider", follow_redirects=True
    )
    assert b"refus" in validate_response.data
    with app.app_context():
        assert Troncon.query.filter_by(course_id=course_id).count() == 0


def test_reimport_replaces_troncons(logged_in_client, app):
    course_id = _create_event_and_course(logged_in_client)

    _upload(logged_in_client, course_id, ["Course1_Tronçon1_Run.gpx", "Course1_Tronçon2_Swim.gpx"])
    logged_in_client.post(f"/orga/courses/{course_id}/import/valider", follow_redirects=True)
    with app.app_context():
        assert Troncon.query.filter_by(course_id=course_id).count() == 2

    _upload(logged_in_client, course_id, ["Course2_Tronçon1_Run.gpx"])
    logged_in_client.post(f"/orga/courses/{course_id}/import/valider", follow_redirects=True)

    with app.app_context():
        troncons = Troncon.query.filter_by(course_id=course_id).all()
        assert len(troncons) == 1
        assert troncons[0].filename == "Course2_Tronçon1_Run.gpx"


def test_import_requires_login(client):
    response = client.get("/orga/courses/1/import", follow_redirects=True)
    assert b"Connexion" in response.data


def test_import_without_files_shows_error(logged_in_client, app):
    course_id = _create_event_and_course(logged_in_client)
    response = logged_in_client.post(
        f"/orga/courses/{course_id}/import",
        data={},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "Sélectionnez".encode() in response.data
    with app.app_context():
        assert not (app.config["UPLOADS_DIR"] / f"course_{course_id}").exists()
