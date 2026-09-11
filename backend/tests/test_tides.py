import math
from datetime import datetime, timedelta, timezone

import pytest

from app.core.tides import (
    CsvMareeInvalideError,
    FuseauInconnuError,
    PointMaree,
    convertir_vers_utc,
    echantillonner,
    interpoler_cosinus,
    parser_csv,
    tendance,
)

T1 = datetime(2027, 7, 12, 6, 0, tzinfo=timezone.utc)
T2 = datetime(2027, 7, 12, 12, 0, tzinfo=timezone.utc)  # 6h plus tard
BASSE_MER = PointMaree(moment=T1, hauteur_m=1.0)
PLEINE_MER = PointMaree(moment=T2, hauteur_m=5.0)
POINTS = [BASSE_MER, PLEINE_MER]


def test_interpoler_cosinus_at_first_extreme():
    assert interpoler_cosinus(POINTS, T1) == pytest.approx(1.0)


def test_interpoler_cosinus_at_second_extreme():
    assert interpoler_cosinus(POINTS, T2) == pytest.approx(5.0)


def test_interpoler_cosinus_at_midpoint_is_the_average():
    milieu = T1 + (T2 - T1) / 2
    assert interpoler_cosinus(POINTS, milieu) == pytest.approx((1.0 + 5.0) / 2)


def test_interpoler_cosinus_matches_formula_at_quarter():
    quart = T1 + (T2 - T1) / 4
    attendu = 1.0 + (5.0 - 1.0) * (1 - math.cos(math.pi * 0.25)) / 2
    assert interpoler_cosinus(POINTS, quart) == pytest.approx(attendu)


def test_interpoler_cosinus_none_before_range():
    assert interpoler_cosinus(POINTS, T1 - timedelta(hours=1)) is None


def test_interpoler_cosinus_none_after_range():
    assert interpoler_cosinus(POINTS, T2 + timedelta(hours=1)) is None


def test_interpoler_cosinus_none_with_a_single_point():
    assert interpoler_cosinus([BASSE_MER], T1) is None


def test_interpoler_cosinus_ease_in_out_near_extremes():
    # Près des extrêmes, la pente doit être plus faible qu'au milieu (repos au voisinage
    # de l'étale, comportement physique attendu d'une marée).
    proche_debut = interpoler_cosinus(POINTS, T1 + timedelta(minutes=1))
    proche_milieu = interpoler_cosinus(POINTS, T1 + timedelta(hours=3) + timedelta(minutes=1))
    pente_debut = proche_debut - 1.0
    pente_milieu = proche_milieu - interpoler_cosinus(POINTS, T1 + timedelta(hours=3))
    assert pente_debut < pente_milieu


def test_tendance_montante():
    assert tendance(POINTS, T1 + timedelta(hours=1)) == "montante"


def test_tendance_descendante():
    points = [PLEINE_MER, PointMaree(moment=T2 + timedelta(hours=6), hauteur_m=1.0)]
    assert tendance(points, T2 + timedelta(hours=1)) == "descendante"


def test_tendance_none_outside_range():
    assert tendance(POINTS, T2 + timedelta(hours=1)) is None


def test_echantillonner_step_and_bounds():
    serie = echantillonner(POINTS, T1, T2, pas_s=3600)
    assert [p.moment for p in serie] == [T1 + timedelta(hours=h) for h in range(7)]
    assert serie[0].hauteur_m == pytest.approx(1.0)
    assert serie[-1].hauteur_m == pytest.approx(5.0)


def test_echantillonner_skips_points_outside_data_range():
    serie = echantillonner(POINTS, T1 - timedelta(hours=2), T2, pas_s=3600)
    assert serie[0].moment == T1


class TestConvertirVersUtc:
    def test_utc_is_a_no_op(self):
        naif = datetime(2027, 7, 12, 9, 0)
        assert convertir_vers_utc(naif, "utc") == naif.replace(tzinfo=timezone.utc)

    def test_utc_plus_1_fixed_offset(self):
        naif = datetime(2027, 7, 12, 9, 0)
        resultat = convertir_vers_utc(naif, "utc+1")
        assert resultat == datetime(2027, 7, 12, 8, 0, tzinfo=timezone.utc)

    def test_heure_legale_summer_is_utc_plus_2(self):
        naif = datetime(2027, 7, 12, 9, 0)  # juillet -> CEST -> UTC+2
        resultat = convertir_vers_utc(naif, "legale")
        assert resultat == datetime(2027, 7, 12, 7, 0, tzinfo=timezone.utc)

    def test_heure_legale_winter_is_utc_plus_1(self):
        naif = datetime(2027, 1, 12, 9, 0)  # janvier -> CET -> UTC+1
        resultat = convertir_vers_utc(naif, "legale")
        assert resultat == datetime(2027, 1, 12, 8, 0, tzinfo=timezone.utc)

    def test_rejects_unknown_timezone(self):
        with pytest.raises(FuseauInconnuError):
            convertir_vers_utc(datetime(2027, 7, 12, 9, 0), "mars")


class TestParserCsv:
    def test_parses_valid_lines(self):
        contenu = "2027-07-12 09:00;3.5\n2027-07-12 09:05;3.6\n"
        resultat = parser_csv(contenu)
        assert resultat == [
            (datetime(2027, 7, 12, 9, 0), 3.5),
            (datetime(2027, 7, 12, 9, 5), 3.6),
        ]

    def test_ignores_blank_lines(self):
        contenu = "2027-07-12 09:00;3.5\n\n   \n2027-07-12 09:05;3.6\n"
        assert len(parser_csv(contenu)) == 2

    def test_accepts_comma_as_decimal_separator(self):
        assert parser_csv("2027-07-12 09:00;3,5")[0][1] == 3.5

    def test_rejects_wrong_column_count(self):
        with pytest.raises(CsvMareeInvalideError):
            parser_csv("2027-07-12 09:00;3.5;extra")

    def test_rejects_invalid_date(self):
        with pytest.raises(CsvMareeInvalideError):
            parser_csv("pas-une-date;3.5")

    def test_rejects_invalid_height(self):
        with pytest.raises(CsvMareeInvalideError):
            parser_csv("2027-07-12 09:00;pas-un-nombre")
