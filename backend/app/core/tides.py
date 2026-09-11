import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DEFAULT_STEP_S = 300  # 5 minutes


@dataclass(frozen=True)
class PointMaree:
    moment: datetime  # timezone-aware (UTC)
    hauteur_m: float


class FuseauInconnuError(ValueError):
    pass


def convertir_vers_utc(moment_naif: datetime, fuseau_source: str) -> datetime:
    """Convertit une date-heure saisie (naïve) vers UTC selon le fuseau de la table source.

    `fuseau_source` : "utc", "utc+1" (décalage fixe, sans heure d'été) ou "legale"
    (heure légale française, Europe/Paris, avec bascule heure d'été/hiver automatique).
    """
    if fuseau_source == "utc":
        return moment_naif.replace(tzinfo=timezone.utc)
    if fuseau_source == "utc+1":
        return moment_naif.replace(tzinfo=timezone(timedelta(hours=1))).astimezone(timezone.utc)
    if fuseau_source == "legale":
        return moment_naif.replace(tzinfo=ZoneInfo("Europe/Paris")).astimezone(timezone.utc)
    raise FuseauInconnuError(f"Fuseau source inconnu : « {fuseau_source} ».")


def _segment_encadrant(
    points_tries: list[PointMaree], moment: datetime
) -> tuple[PointMaree, PointMaree] | None:
    if len(points_tries) < 2:
        return None
    if moment < points_tries[0].moment or moment > points_tries[-1].moment:
        return None
    for p1, p2 in zip(points_tries, points_tries[1:]):
        if p1.moment <= moment <= p2.moment:
            return p1, p2
    return None


def interpoler_cosinus(points: list[PointMaree], moment: datetime) -> float | None:
    """Hauteur d'eau interpolée à `moment`, en cosinus entre les deux extrêmes encadrants.

    h(t) = h1 + (h2 - h1) * (1 - cos(pi * (t - t1) / (t2 - t1))) / 2

    Retourne None si moins de 2 points sont fournis ou si `moment` est hors de la
    plage couverte par `points` (pas d'extrapolation) — voir §5 du cahier des
    charges : il faut idéalement saisir les extrêmes de la veille et du lendemain
    pour couvrir les bords de la plage horaire simulée.
    """
    points_tries = sorted(points, key=lambda p: p.moment)
    segment = _segment_encadrant(points_tries, moment)
    if segment is None:
        return None

    p1, p2 = segment
    if p1.moment == p2.moment:
        return p1.hauteur_m

    ratio_temps = (moment - p1.moment).total_seconds() / (p2.moment - p1.moment).total_seconds()
    return p1.hauteur_m + (p2.hauteur_m - p1.hauteur_m) * (1 - math.cos(math.pi * ratio_temps)) / 2


def tendance(points: list[PointMaree], moment: datetime) -> str | None:
    """« montante » ou « descendante » selon le sens du segment encadrant `moment`."""
    points_tries = sorted(points, key=lambda p: p.moment)
    segment = _segment_encadrant(points_tries, moment)
    if segment is None:
        return None

    p1, p2 = segment
    if p2.hauteur_m == p1.hauteur_m:
        return None
    return "montante" if p2.hauteur_m > p1.hauteur_m else "descendante"


def echantillonner(
    points: list[PointMaree], debut: datetime, fin: datetime, pas_s: int = DEFAULT_STEP_S
) -> list[PointMaree]:
    """Échantillonne la hauteur interpolée toutes les pas_s secondes entre debut et fin (§5)."""
    if debut > fin:
        return []

    resultat: list[PointMaree] = []
    moment = debut
    while moment <= fin:
        hauteur = interpoler_cosinus(points, moment)
        if hauteur is not None:
            resultat.append(PointMaree(moment=moment, hauteur_m=hauteur))
        moment += timedelta(seconds=pas_s)
    return resultat


class CsvMareeInvalideError(ValueError):
    pass


def parser_csv(contenu: str) -> list[tuple[datetime, float]]:
    """Parse un CSV `datetime;hauteur_m` (Option B, §5). Une ligne par mesure, dates naïves."""
    resultat: list[tuple[datetime, float]] = []
    for numero, ligne in enumerate(contenu.splitlines(), start=1):
        ligne = ligne.strip()
        if not ligne:
            continue
        morceaux = ligne.split(";")
        if len(morceaux) != 2:
            raise CsvMareeInvalideError(
                f"Ligne {numero} invalide : « {ligne} » (attendu datetime;hauteur_m)."
            )
        moment_brut, hauteur_brute = morceaux
        try:
            moment = datetime.fromisoformat(moment_brut.strip().replace(" ", "T"))
        except ValueError as exc:
            raise CsvMareeInvalideError(
                f"Ligne {numero} : date invalide « {moment_brut} »."
            ) from exc
        try:
            hauteur = float(hauteur_brute.strip().replace(",", "."))
        except ValueError as exc:
            raise CsvMareeInvalideError(
                f"Ligne {numero} : hauteur invalide « {hauteur_brute} »."
            ) from exc
        resultat.append((moment, hauteur))
    return resultat
