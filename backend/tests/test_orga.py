from app.extensions import db
from app.models import Course, Event


def _create_event(client):
    return client.post(
        "/orga/evenement",
        data={"name": "Swimrun de Saint-Pabu", "date": "2027-07-12"},
        follow_redirects=True,
    )


def _create_course(client, name="Course XS", color="#1d4ed8", start_time="09:00"):
    return client.post(
        "/orga/courses/nouvelle",
        data={"name": name, "color": color, "start_time": start_time},
        follow_redirects=True,
    )


def test_create_event(logged_in_client, app):
    response = _create_event(logged_in_client)
    assert response.status_code == 200
    with app.app_context():
        event = Event.query.first()
        assert event is not None
        assert event.name == "Swimrun de Saint-Pabu"
        assert event.timezone == "Europe/Paris"


def test_create_course_requires_event_first(logged_in_client):
    response = logged_in_client.get("/orga/courses/nouvelle", follow_redirects=True)
    assert b"Configurez" in response.data


def test_create_and_edit_course(logged_in_client, app):
    _create_event(logged_in_client)
    _create_course(logged_in_client)

    with app.app_context():
        course = Course.query.first()
        assert course is not None
        assert course.name == "Course XS"
        assert course.color == "#1d4ed8"
        course_id = course.id

    response = logged_in_client.post(
        f"/orga/courses/{course_id}/modifier",
        data={"name": "Course XS modifiée", "color": "#16a34a", "start_time": "09:30"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        course = db.session.get(Course, course_id)
        assert course.name == "Course XS modifiée"
        assert course.color == "#16a34a"


def test_max_three_courses_per_event(logged_in_client, app):
    _create_event(logged_in_client)
    for i in range(3):
        response = _create_course(logged_in_client, name=f"Course {i}")
        assert response.status_code == 200

    response = _create_course(logged_in_client, name="Course en trop")
    assert b"Maximum 3 courses" in response.data

    with app.app_context():
        assert Course.query.count() == 3


def test_delete_course(logged_in_client, app):
    _create_event(logged_in_client)
    _create_course(logged_in_client)
    with app.app_context():
        course_id = Course.query.first().id

    logged_in_client.post(f"/orga/courses/{course_id}/supprimer", follow_redirects=True)
    with app.app_context():
        assert db.session.get(Course, course_id) is None


def test_course_rejects_invalid_color(logged_in_client):
    _create_event(logged_in_client)
    response = _create_course(logged_in_client, color="not-a-color")
    assert "hexadécimale".encode() in response.data


def _create_course_with_paces(client, **paces):
    _create_event(client)
    data = {"name": "Course XS", "color": "#1d4ed8", "start_time": "09:00", **paces}
    return client.post("/orga/courses/nouvelle", data=data, follow_redirects=True)


def test_course_accepts_valid_paces(logged_in_client, app):
    response = _create_course_with_paces(
        logged_in_client,
        premier_allure_course="5:00",
        premier_allure_nage="2:00",
        dernier_allure_course="7:00",
        dernier_allure_nage="3:00",
    )
    assert response.status_code == 200
    with app.app_context():
        course = Course.query.first()
        assert course.premier_allure_course_s == 300
        assert course.premier_allure_nage_s == 120
        assert course.dernier_allure_course_s == 420
        assert course.dernier_allure_nage_s == 180


def test_course_rejects_premier_slower_than_dernier(logged_in_client, app):
    response = _create_course_with_paces(
        logged_in_client,
        premier_allure_course="7:00",
        premier_allure_nage="2:00",
        dernier_allure_course="5:00",
        dernier_allure_nage="3:00",
    )
    assert b"plus rapide" in response.data
    with app.app_context():
        assert Course.query.count() == 0


def test_course_allows_paces_left_empty(logged_in_client, app):
    response = _create_course_with_paces(logged_in_client)
    assert response.status_code == 200
    with app.app_context():
        course = Course.query.first()
        assert course is not None
        assert course.premier_allure_course_s is None


def test_edit_course_prefills_paces(logged_in_client, app):
    _create_course_with_paces(
        logged_in_client,
        premier_allure_course="5:00",
        premier_allure_nage="2:00",
        dernier_allure_course="7:00",
        dernier_allure_nage="3:00",
    )
    with app.app_context():
        course_id = Course.query.first().id

    response = logged_in_client.get(f"/orga/courses/{course_id}/modifier")
    assert b'value="5:00"' in response.data
    assert b'value="3:00"' in response.data
