from dataclasses import dataclass

from app.core.geometry import project_equirectangular, resample_by_distance

DEFAULT_RESAMPLE_STEP_M = 5.0
DEFAULT_PROXIMITY_M = 12.0
DEFAULT_MIN_GAP_M = 200.0
DEFAULT_MIN_SEGMENT_LENGTH_M = 30.0

# Tolérance (en nombre de points rééchantillonnés) pour considérer que deux paires
# proches appartiennent au même couloir de superposition plutôt qu'à deux couloirs distincts.
CORRIDOR_INDEX_TOLERANCE = 2


@dataclass(frozen=True)
class Passage:
    start_distance_m: float
    end_distance_m: float


@dataclass(frozen=True)
class OverlapGroup:
    """Un même lieu physique traversé plusieurs fois, avec ses passages triés chronologiquement."""

    passages: list[Passage]


def detect_multiple_passages(
    points: list[tuple[float, float, float]],
    *,
    proximity_m: float = DEFAULT_PROXIMITY_M,
    min_gap_m: float = DEFAULT_MIN_GAP_M,
    min_segment_length_m: float = DEFAULT_MIN_SEGMENT_LENGTH_M,
    resample_step_m: float = DEFAULT_RESAMPLE_STEP_M,
) -> list[OverlapGroup]:
    """Détecte les portions d'un tracé empruntées plusieurs fois.

    points : liste (lat, lon, distance_cumulee_m) triée par distance croissante,
    typiquement le tracé complet assemblé d'une course (voir gpx_import.assemble_course).

    Principe : on rééchantillonne tous les resample_step_m, puis pour chaque point on
    cherche son plus proche voisin spatial (< proximity_m) parmi les points éloignés
    sur le tracé (> min_gap_m) — une seule meilleure correspondance par point, pas
    toutes les correspondances possibles, sans quoi une ligne droite aller-retour
    produit un faisceau de correspondances voisines qui fragmente artificiellement
    un seul couloir en plusieurs. Les correspondances (i, best_j) forment alors une
    diagonale continue dans la grille des indices : un aller-retour donne une
    anti-diagonale continue, un croisement de type « boucle en 8 » donne une
    diagonale localisée et courte. Chaque couloir se traduit par deux intervalles
    d'indices, donc deux passages.
    """
    resampled = resample_by_distance(points, resample_step_m)
    n = len(resampled)
    if n < 2:
        return []

    ref_lat, ref_lon = resampled[0][0], resampled[0][1]
    xy = project_equirectangular([(lat, lon) for lat, lon, _ in resampled], ref_lat, ref_lon)
    dist = [d for _, _, d in resampled]
    proximity_sq = proximity_m * proximity_m

    best_match: dict[int, tuple[int, float]] = {}  # index -> (partenaire le plus proche, dist²)

    def consider(a: int, b: int, dist_sq: float) -> None:
        current = best_match.get(a)
        if current is None or dist_sq < current[1]:
            best_match[a] = (b, dist_sq)

    for i in range(n):
        xi, yi = xy[i]
        di = dist[i]
        for j in range(i + 1, n):
            if dist[j] - di <= min_gap_m:
                continue
            xj, yj = xy[j]
            dx, dy = xi - xj, yi - yj
            dist_sq = dx * dx + dy * dy
            if dist_sq <= proximity_sq:
                consider(i, j, dist_sq)
                consider(j, i, dist_sq)

    if not best_match:
        return []

    pairs = sorted((i, j) for i, (j, _) in best_match.items())

    corridors: list[list[tuple[int, int]]] = []
    for pair in pairs:
        i, j = pair
        if corridors:
            last_i, last_j = corridors[-1][-1]
            i_close = i - last_i <= CORRIDOR_INDEX_TOLERANCE
            j_close = abs(j - last_j) <= CORRIDOR_INDEX_TOLERANCE
            if i_close and j_close:
                corridors[-1].append(pair)
                continue
        corridors.append([pair])

    groups: list[OverlapGroup] = []
    for corridor in corridors:
        is_ = [p[0] for p in corridor]
        js = [p[1] for p in corridor]
        seg_a = (min(is_), max(is_))
        seg_b = (min(js), max(js))
        len_a = dist[seg_a[1]] - dist[seg_a[0]]
        len_b = dist[seg_b[1]] - dist[seg_b[0]]
        if len_a < min_segment_length_m or len_b < min_segment_length_m:
            continue
        passages = sorted(
            [Passage(dist[seg_a[0]], dist[seg_a[1]]), Passage(dist[seg_b[0]], dist[seg_b[1]])],
            key=lambda p: p.start_distance_m,
        )
        groups.append(OverlapGroup(passages))

    groups = _merge_overlapping_groups(groups, merge_gap_m=2 * resample_step_m)
    groups.sort(key=lambda g: g.passages[0].start_distance_m)
    return groups


def _coalesce_passages(passages: list[Passage], merge_gap_m: float) -> list[Passage]:
    ordered = sorted(passages, key=lambda p: p.start_distance_m)
    coalesced: list[Passage] = []
    for p in ordered:
        if coalesced and p.start_distance_m <= coalesced[-1].end_distance_m + merge_gap_m:
            last = coalesced[-1]
            end = max(last.end_distance_m, p.end_distance_m)
            coalesced[-1] = Passage(last.start_distance_m, end)
        else:
            coalesced.append(p)
    return coalesced


def _merge_overlapping_groups(groups: list[OverlapGroup], merge_gap_m: float) -> list[OverlapGroup]:
    """Fusionne les groupes qui décrivent en réalité le même couloir physique.

    Près d'un point de rebroussement (demi-tour d'un aller-retour), la correspondance
    au plus proche voisin est instable sur quelques points (la vraie symétrique est
    exclue par min_gap_m), ce qui peut scinder un seul couloir en deux groupes quasi
    identiques. On les recolle ici si l'union de leurs passages redonne le même
    nombre de passages qu'au départ (c'est-à-dire que les groupes ne faisaient que
    décrire deux fois la même chose, à quelques mètres près).
    """
    merged = list(groups)
    changed = True
    while changed:
        changed = False
        for a in range(len(merged)):
            for b in range(a + 1, len(merged)):
                combined = _coalesce_passages(merged[a].passages + merged[b].passages, merge_gap_m)
                if len(combined) == len(merged[a].passages) == len(merged[b].passages):
                    merged[a] = OverlapGroup(combined)
                    del merged[b]
                    changed = True
                    break
            if changed:
                break
    return merged
