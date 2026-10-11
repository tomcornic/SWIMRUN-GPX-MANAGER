from html import unescape
from io import BytesIO

import pytest

from app.models import MareeReleve


def _create_event(client) -> None:
    client.post(
        "/orga/evenement",
        data={"name": "Swimrun de Saint-Pabu", "date": "2027-07-12"},
        follow_redirects=True,
    )


def _ajouter(client, hauteur: str, heure: str = "06:12"):
    return client.post(
        "/orga/maree/ajouter",
        data={
            "date": "2027-07-12",
            "heure": heure,
            "hauteur_m": hauteur,
            "type": "pm",
            "fuseau_source": "legale",
        },
        follow_redirects=True,
    )


@pytest.mark.parametrize(
    ("saisie", "attendu"),
    [("5.80", 5.8), ("5,80", 5.8), (" 1,35 ", 1.35), ("0", 0.0), ("0,00", 0.0), ("-0,2", -0.2)],
)
def test_maree_ajouter_accepte_virgule_et_zero(logged_in_client, app, saisie, attendu):
    _create_event(logged_in_client)
    response = _ajouter(logged_in_client, saisie)
    assert "Point de marée ajouté.".encode() in response.data
    with app.app_context():
        assert MareeReleve.query.one().hauteur_m == pytest.approx(attendu)


@pytest.mark.parametrize("saisie", ["abc", "5,8,1", "nan", "inf"])
def test_maree_ajouter_hauteur_invalide_message_explicite(logged_in_client, app, saisie):
    _create_event(logged_in_client)
    response = _ajouter(logged_in_client, saisie)
    assert b"Hauteur invalide" in response.data
    with app.app_context():
        assert MareeReleve.query.count() == 0


def test_maree_ajouter_champs_vides_messages_en_francais(logged_in_client, app):
    _create_event(logged_in_client)
    response = logged_in_client.post(
        "/orga/maree/ajouter",
        data={"date": "", "heure": "", "hauteur_m": "", "type": "pm", "fuseau_source": "legale"},
        follow_redirects=True,
    )
    page = unescape(response.get_data(as_text=True))
    for message in ("La date est requise.", "L'heure est requise.", "La hauteur est requise."):
        assert message in page
    assert "This field is required" not in page
    with app.app_context():
        assert MareeReleve.query.count() == 0


def _importer_csv(client, contenu: bytes):
    return client.post(
        "/orga/maree/importer-csv",
        data={"fichier": (BytesIO(contenu), "maree.csv"), "fuseau_source": "legale"},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


def test_maree_csv_avec_bom_excel(logged_in_client, app):
    _create_event(logged_in_client)
    contenu = "﻿2027-07-12 09:00;3,5\n2027-07-12 10:00;4,1\n".encode()
    response = _importer_csv(logged_in_client, contenu)
    assert "2 mesure(s) importée(s).".encode() in response.data
    with app.app_context():
        assert MareeReleve.query.count() == 2


def test_maree_csv_non_utf8_message_explicite(logged_in_client, app):
    _create_event(logged_in_client)
    response = _importer_csv(logged_in_client, "2027-07-12 09:00;3.5 # marée\n".encode("latin-1"))
    assert b"UTF-8 est attendu" in response.data
    with app.app_context():
        assert MareeReleve.query.count() == 0
