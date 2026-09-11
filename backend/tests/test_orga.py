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
