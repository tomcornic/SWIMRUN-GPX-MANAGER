import json


def test_index_works_without_any_publication(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Swimrun de Saint-Pabu" in response.data


def test_index_uses_published_meta_for_og_tags(client, app):
    published_dir = app.config["PUBLISHED_DIR"]
    published_dir.mkdir(parents=True, exist_ok=True)
    (published_dir / "meta.json").write_text(
        json.dumps({"nom": "Course Test", "date": "2027-07-12", "courses": []})
    )

    response = client.get("/")
    assert b"Course Test" in response.data


def test_fichier_publie_serves_existing_file(client, app):
    published_dir = app.config["PUBLISHED_DIR"]
    published_dir.mkdir(parents=True, exist_ok=True)
    (published_dir / "meta.json").write_text(json.dumps({"nom": "Test"}))

    response = client.get("/publie/meta.json")
    assert response.status_code == 200
    assert response.get_json() == {"nom": "Test"}


def test_fichier_publie_404_for_missing_file(client, app):
    app.config["PUBLISHED_DIR"].mkdir(parents=True, exist_ok=True)
    response = client.get("/publie/course-999.geojson")
    assert response.status_code == 404


def test_public_routes_require_no_login(client):
    # Contrairement à /orga/*, aucune route publique ne doit rediriger vers le login.
    for url in ("/", "/publie/meta.json"):
        response = client.get(url)
        assert response.status_code != 302
