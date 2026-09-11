from dataclasses import dataclass


@dataclass(frozen=True)
class TronconPublic:
    numero: int
    type: str
    longueur_m: float
    points: list[tuple[float, float]]  # (lat, lon)


@dataclass(frozen=True)
class PassagePublic:
    debut_m: float
    fin_m: float


@dataclass(frozen=True)
class GroupePassagesPublic:
    passages: list[PassagePublic]


@dataclass(frozen=True)
class CoursePublic:
    id: int
    nom: str
    couleur: str
    troncons: list[TronconPublic]
    passages_multiples: list[GroupePassagesPublic]


@dataclass(frozen=True)
class PoiPublic:
    id: int
    type: str
    nom: str
    description: str
    lat: float
    lon: float
    cote_passage: str | None
    distance_m: float


def construire_meta(nom_evenement: str, date_evenement: str, courses: list[CoursePublic]) -> dict:
    """Métadonnées publiques de l'événement. `genere_le` est ajouté par l'appelant
    (horodatage non déterministe, donc hors de ce module pur)."""
    return {
        "nom": nom_evenement,
        "date": date_evenement,
        "courses": [{"id": c.id, "nom": c.nom, "couleur": c.couleur} for c in courses],
    }


def construire_course_geojson(course: CoursePublic) -> dict:
    """GeoJSON public d'une course : tracé, tronçons (type/bornes), passages multiples.

    Ne contient jamais d'allure ni de donnée de simulation (§5 : découplage privé/public).
    """
    coordinates: list[list[float]] = []
    troncons_meta = []
    cumul = 0.0
    for troncon in course.troncons:
        coordinates.extend([lon, lat] for lat, lon in troncon.points)
        troncons_meta.append(
            {
                "numero": troncon.numero,
                "type": troncon.type,
                "debut_m": cumul,
                "fin_m": cumul + troncon.longueur_m,
            }
        )
        cumul += troncon.longueur_m

    return {
        "type": "Feature",
        "properties": {
            "id": course.id,
            "nom": course.nom,
            "couleur": course.couleur,
            "troncons": troncons_meta,
            "passages_multiples": [
                {"passages": [{"debut_m": p.debut_m, "fin_m": p.fin_m} for p in groupe.passages]}
                for groupe in course.passages_multiples
            ],
        },
        "geometry": {"type": "LineString", "coordinates": coordinates},
    }


def construire_pois_json(pois: list[PoiPublic]) -> list[dict]:
    """JSON public des POI d'une course. Jamais de donnée privée (allure, simulation)."""
    return [
        {
            "id": poi.id,
            "type": poi.type,
            "nom": poi.nom,
            "description": poi.description,
            "lat": poi.lat,
            "lon": poi.lon,
            "cote_passage": poi.cote_passage,
            "distance_m": poi.distance_m,
        }
        for poi in pois
    ]
