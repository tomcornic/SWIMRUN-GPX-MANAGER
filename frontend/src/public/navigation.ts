import type { CourseParcours, GroupePassagesParcours, PoiParcours, TronconParcours } from "./parcours";

export interface PositionTroncon {
  troncon: TronconParcours;
  index: number;
  total: number;
  distanceRestanteM: number;
}

/** Le tronçon (et sa position dans la séquence) à une distance donnée sur le parcours. */
export function tronconALaDistance(course: CourseParcours, distanceM: number): PositionTroncon | null {
  const troncons = course.troncons;
  if (troncons.length === 0) return null;

  const clamped = Math.min(Math.max(distanceM, 0), course.longueurTotaleM);
  const index = troncons.findIndex((t) => clamped >= t.debutM && clamped <= t.finM);
  const i = index === -1 ? troncons.length - 1 : index;
  const troncon = troncons[i];

  return { troncon, index: i, total: troncons.length, distanceRestanteM: troncon.finM - clamped };
}

export interface PoiProche {
  poi: PoiParcours;
  distanceM: number;
}

/** Le prochain POI en avant (ou égal) à la distance donnée, avec la distance qui le sépare. */
export function prochainPoi(pois: PoiParcours[], distanceM: number): PoiProche | null {
  const devant = pois.filter((p) => p.distanceM >= distanceM).sort((a, b) => a.distanceM - b.distanceM);
  if (devant.length === 0) return null;
  return { poi: devant[0], distanceM: devant[0].distanceM - distanceM };
}

export interface PassageActif {
  groupeIndex: number;
  numeroPassage: number; // 1-indexé
  totalPassages: number;
}

/** Le passage actif (et son numéro dans la séquence) si la distance tombe dans une
 * portion empruntée plusieurs fois, sinon null (§6 : mise en avant du passage actif). */
export function passageActifA(groupes: GroupePassagesParcours[], distanceM: number): PassageActif | null {
  for (let groupeIndex = 0; groupeIndex < groupes.length; groupeIndex++) {
    const passages = groupes[groupeIndex].passages;
    for (let i = 0; i < passages.length; i++) {
      if (distanceM >= passages[i].debutM && distanceM <= passages[i].finM) {
        return { groupeIndex, numeroPassage: i + 1, totalPassages: passages.length };
      }
    }
  }
  return null;
}

function ordinal(n: number): string {
  return n === 1 ? "1er" : `${n}e`;
}

/** Message contextuel affiché quand le curseur est dans une portion multiple (§6). */
export function messagePassage(actif: PassageActif): string {
  return `${ordinal(actif.numeroPassage)} passage — portion empruntée ${actif.totalPassages} fois.`;
}
