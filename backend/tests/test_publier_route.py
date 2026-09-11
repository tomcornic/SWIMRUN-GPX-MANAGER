import json
from io import BytesIO
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def _setup_course_with_track_and_poi(client) -> int:
    client.post(
        "/orga/evenement",
        data={"name": "Swimrun de Saint-Pabu", "date": "2027-07-12"},
        follow_redirects=True,
    )
    client.post(
        "/orga/courses/nouvelle",
        data={
            "name": "Course XS",
            "color": "#1d4ed8",
            "start_time": "09:00",
            "premier_allure_course": "5:00",
            "premier_allure_nage": "2:00",
            "dernier_allure_course": "7:00",
            "dernier_allure_nage": "3:00",
        },
        follow_redirects=True,
    )
    course_id = 1

    files = [
        (BytesIO((DEMO_DIR / name).read_bytes()), name)
        for name in ["Course1_Tronçon1_Run.gpx", "Course1_Tronçon2_Swim.gpx"]
    ]
    client.post(
        f"/orga/courses/{course_id}/import",
        data={"fichiers": files},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    client.post(f"/orga/courses/{course_id}/import/valider", follow_redirects=True)

    client.post(
        "/orga/poi/nouveau",
        data={
            "type": "ravitaillement",
            "nom": "Ravito",
            "description": "Eau",
            "lat": "48.565",
            "lon": "-4.596",
            "cote_passage": "",
            "courses": str(course_id),
        },
        follow_redirects=True,
    )
    return course_id


def test_publier_generates_expected_files(logged_in_client, app):
    course_id = _setup_course_with_track_and_poi(logged_in_client)

    response = logged_in_client.post("/orga/publier", follow_redirects=True)
    assert response.status_code == 200

    published_dir = app.config["PUBLISHED_DIR"]
    assert (published_dir / "meta.json").exists()
    assert (published_dir / f"course-{course_id}.geojson").exists()
    assert (published_dir / f"pois-{course_id}.json").exists()


def test_publier_never_leaks_private_data(logged_in_client, app):
    course_id = _setup_course_with_track_and_poi(logged_in_client)
    logged_in_client.post("/orga/publier", follow_redirects=True)

    published_dir = app.config["PUBLISHED_DIR"]
    for filename in ("meta.json", f"course-{course_id}.geojson", f"pois-{course_id}.json"):
        contenu = (published_dir / filename).read_text().lower()
        for mot_interdit in ("allure", "profil", "simulation"):
            assert mot_interdit not in contenu, f"{filename} contient « {mot_interdit} »"


def test_publier_meta_has_timestamp(logged_in_client, app):
    _setup_course_with_track_and_poi(logged_in_client)
    logged_in_client.post("/orga/publier", follow_redirects=True)

    meta = json.loads((app.config["PUBLISHED_DIR"] / "meta.json").read_text())
    assert "genere_le" in meta
    assert meta["courses"][0]["nom"] == "Course XS"


def test_publier_poi_distance_matches_projection(logged_in_client, app):
    course_id = _setup_course_with_track_and_poi(logged_in_client)
    logged_in_client.post("/orga/publier", follow_redirects=True)

    pois = json.loads((app.config["PUBLISHED_DIR"] / f"pois-{course_id}.json").read_text())
    assert len(pois) == 1
    # Le POI a été placé exactement sur le point de départ du tracé de démo.
    assert pois[0]["distance_m"] == 0.0


def test_publier_requires_event(logged_in_client):
    response = logged_in_client.post("/orga/publier", follow_redirects=True)
    assert b"Configurez" in response.data
