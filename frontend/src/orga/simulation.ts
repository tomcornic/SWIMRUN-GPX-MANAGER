export type TypeTroncon = "run" | "swim";

export interface Troncon {
  numero: number;
  type: TypeTroncon;
  longueurM: number;
}

export interface Course {
  troncons: Troncon[]; // triés par numero
}

/** Allure d'un coureur : secondes par km (course à pied) et par 100 m (natation). */
export interface Profil {
  courseSParKm: number;
  nageSPar100m: number;
}

export interface AllureCourse {
  premier: Profil;
  dernier: Profil;
}

export interface TronconTiming {
  numero: number;
  type: TypeTroncon;
  entreeS: number;
  sortieS: number;
  entreeDistanceM: number;
  sortieDistanceM: number;
}

/**
 * Pour chaque tronçon, heure d'entrée et de sortie = cumul de longueur × allure du type
 * (§5 du cahier des charges).
 */
export function timeline(course: Course, profil: Profil): TronconTiming[] {
  let tempsS = 0;
  let distanceM = 0;
  const result: TronconTiming[] = [];

  for (const troncon of course.troncons) {
    const allureSParM =
      troncon.type === "run" ? profil.courseSParKm / 1000 : profil.nageSPar100m / 100;
    const dureeS = troncon.longueurM * allureSParM;
    const entreeS = tempsS;
    const entreeDistanceM = distanceM;
    tempsS += dureeS;
    distanceM += troncon.longueurM;
    result.push({
      numero: troncon.numero,
      type: troncon.type,
      entreeS,
      sortieS: tempsS,
      entreeDistanceM,
      sortieDistanceM: distanceM,
    });
  }

  return result;
}

/**
 * Distance parcourue sur le tracé à l'instant t (secondes depuis le départ).
 * Avant le départ : pas de position (null). Après l'arrivée : bloqué à la distance totale.
 */
export function distanceAt(course: Course, profil: Profil, t: number): number | null {
  if (t < 0) return null;

  const segments = timeline(course, profil);
  if (segments.length === 0) return 0;

  const dernier = segments[segments.length - 1];
  if (t >= dernier.sortieS) return dernier.sortieDistanceM;

  for (const segment of segments) {
    if (t <= segment.sortieS) {
      const dureeS = segment.sortieS - segment.entreeS;
      const ratio = dureeS === 0 ? 0 : (t - segment.entreeS) / dureeS;
      return segment.entreeDistanceM + ratio * (segment.sortieDistanceM - segment.entreeDistanceM);
    }
  }

  return dernier.sortieDistanceM;
}

export interface Plage {
  /** Position du dernier coureur (arrière du peloton), null s'il n'est pas encore parti. */
  debutM: number | null;
  /** Position du premier coureur (tête du peloton), null s'il n'est pas encore parti. */
  finM: number | null;
}

/** La « plage » d'une course à l'instant t = portion du tracé entre distanceAt(dernier) et distanceAt(premier). */
export function plageAt(course: Course, allure: AllureCourse, t: number): Plage {
  return {
    debutM: distanceAt(course, allure.dernier, t),
    finM: distanceAt(course, allure.premier, t),
  };
}

export type EtatCoureur = "pas_parti" | "en_course" | "termine";

export function etatCoureur(course: Course, profil: Profil, t: number): EtatCoureur {
  const segments = timeline(course, profil);
  if (segments.length === 0 || t < 0) return "pas_parti";
  const dernier = segments[segments.length - 1];
  if (t >= dernier.sortieS) return "termine";
  return "en_course";
}

/** Longueur totale du tracé, dérivée des tronçons. */
export function longueurTotaleM(course: Course): number {
  return course.troncons.reduce((total, t) => total + t.longueurM, 0);
}

/** Le tronçon dans lequel se trouve le coureur à l'instant t (null si pas encore parti). */
export function tronconActuel(course: Course, profil: Profil, t: number): TronconTiming | null {
  if (t < 0) return null;
  const segments = timeline(course, profil);
  if (segments.length === 0) return null;
  for (const segment of segments) {
    if (t < segment.sortieS) return segment;
  }
  return segments[segments.length - 1];
}

/**
 * Validation §5 : le premier doit être plus rapide que le dernier sur chaque discipline.
 * Retourne la liste des messages d'erreur (vide si l'allure est valide).
 */
export function validerAllure(allure: AllureCourse): string[] {
  const erreurs: string[] = [];
  if (allure.premier.courseSParKm >= allure.dernier.courseSParKm) {
    erreurs.push("L'allure du premier doit être plus rapide que celle du dernier, en course à pied.");
  }
  if (allure.premier.nageSPar100m >= allure.dernier.nageSPar100m) {
    erreurs.push("L'allure du premier doit être plus rapide que celle du dernier, en natation.");
  }
  return erreurs;
}
