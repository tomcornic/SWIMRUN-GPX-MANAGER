import json

from app.core.publish import (
    CoursePublic,
    GroupePassagesPublic,
    PassagePublic,
    PoiPublic,
    TronconPublic,
    construire_course_geojson,
    construire_meta,
    construire_pois_json,
)

TRONCONS = [
    TronconPublic(
        numero=1, type="run", longueur_m=100.0, points=[(48.565, -4.596), (48.566, -4.596)]
    ),
    TronconPublic(
        numero=2, type="swim", longueur_m=50.0, points=[(48.566, -4.596), (48.567, -4.596)]
    ),
]

COURSE = CoursePublic(
    id=1,
    nom="Course XS",
    couleur="#1d4ed8",
    troncons=TRONCONS,
    passages_multiples=[GroupePassagesPublic(passages=[PassagePublic(debut_m=10.0, fin_m=40.0)])],
)


def test_construire_meta_lists_courses():
    meta = construire_meta("Swimrun de Saint-Pabu", "2027-07-12", [COURSE])
    assert meta["nom"] == "Swimrun de Saint-Pabu"
    assert meta["date"] == "2027-07-12"
    assert meta["courses"] == [{"id": 1, "nom": "Course XS", "couleur": "#1d4ed8"}]


def test_construire_meta_never_leaks_private_data():
    meta = construire_meta("Swimrun de Saint-Pabu", "2027-07-12", [COURSE])
    contenu = json.dumps(meta).lower()
    for mot_interdit in ("allure", "profil", "simulation", "premier_allure", "dernier_allure"):
        assert mot_interdit not in contenu


def test_construire_course_geojson_structure():
    geojson = construire_course_geojson(COURSE)
    assert geojson["type"] == "Feature"
    assert geojson["geometry"]["type"] == "LineString"
    # 2 points par tronçon, 2 tronçons.
    assert len(geojson["geometry"]["coordinates"]) == 4
    assert geojson["properties"]["troncons"] == [
        {"numero": 1, "type": "run", "debut_m": 0.0, "fin_m": 100.0},
        {"numero": 2, "type": "swim", "debut_m": 100.0, "fin_m": 150.0},
    ]


def test_construire_course_geojson_includes_multiple_passages():
    geojson = construire_course_geojson(COURSE)
    assert geojson["properties"]["passages_multiples"] == [
        {"passages": [{"debut_m": 10.0, "fin_m": 40.0}]}
    ]


def test_construire_course_geojson_never_leaks_private_data():
    geojson = construire_course_geojson(COURSE)
    contenu = json.dumps(geojson).lower()
    for mot_interdit in ("allure", "profil", "simulation"):
        assert mot_interdit not in contenu


def test_construire_pois_json():
    pois = [
        PoiPublic(
            id=1,
            type="ravitaillement",
            nom="Ravito plage",
            description="Eau et fruits secs",
            lat=48.565,
            lon=-4.596,
            cote_passage=None,
            distance_m=250.0,
        )
    ]
    resultat = construire_pois_json(pois)
    assert resultat == [
        {
            "id": 1,
            "type": "ravitaillement",
            "nom": "Ravito plage",
            "description": "Eau et fruits secs",
            "lat": 48.565,
            "lon": -4.596,
            "cote_passage": None,
            "distance_m": 250.0,
        }
    ]
