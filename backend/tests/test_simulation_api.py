from io import BytesIO
from pathlib import Path

from app.models import Course

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def _setup_course_with_track_and_paces(client) -> int:
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
    with client.application.app_context():
        course_id = Course.query.first().id

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
    return course_id


def test_simulation_json_requires_login(client):
    response = client.get("/orga/courses/1/simulation.json", follow_redirects=True)
    assert b"Connexion" in response.data


def test_simulation_json_full_payload(logged_in_client, app):
    course_id = _setup_course_with_track_and_paces(logged_in_client)

    response = logged_in_client.get(f"/orga/courses/{course_id}/simulation.json")
    data = response.get_json()

    assert data["nom"] == "Course XS"
    assert data["heure_depart"] == "09:00:00"
    assert [t["numero"] for t in data["troncons"]] == [1, 2]
    assert [t["type"] for t in data["troncons"]] == ["run", "swim"]
    assert data["allures"] == {
        "premier": {"course_s_par_km": 300, "nage_s_par_100m": 120},
        "dernier": {"course_s_par_km": 420, "nage_s_par_100m": 180},
    }
    assert data["trace"]["type"] == "LineString"
    assert len(data["trace"]["coordinates"]) > 0


def test_simulation_json_allures_null_when_incomplete(logged_in_client, app):
    logged_in_client.post(
        "/orga/evenement",
        data={"name": "Swimrun de Saint-Pabu", "date": "2027-07-12"},
        follow_redirects=True,
    )
    logged_in_client.post(
        "/orga/courses/nouvelle",
        data={"name": "Course XS", "color": "#1d4ed8", "start_time": "09:00"},
        follow_redirects=True,
    )
    with app.app_context():
        course_id = Course.query.first().id

    response = logged_in_client.get(f"/orga/courses/{course_id}/simulation.json")
    assert response.get_json()["allures"] is None
