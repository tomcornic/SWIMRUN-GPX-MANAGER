/** Parse une heure "HH:MM:SS" ou "HH:MM" en secondes depuis minuit. */
export function heureVersSecondes(heure: string): number {
  const parts = heure.split(":").map(Number);
  const [h, m, s] = [parts[0] ?? 0, parts[1] ?? 0, parts[2] ?? 0];
  return h * 3600 + m * 60 + s;
}

/** Formate des secondes (depuis minuit, éventuellement négatives) en "HH:MM:SS". */
export function formaterHMS(totalSecondes: number): string {
  const signe = totalSecondes < 0 ? "-" : "";
  const abs = Math.round(Math.abs(totalSecondes));
  const h = Math.floor(abs / 3600);
  const m = Math.floor((abs % 3600) / 60);
  const s = abs % 60;
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${signe}${pad(h)}:${pad(m)}:${pad(s)}`;
}

/** Formate une durée en secondes en texte court ("3 min", "1 h 20 min"). */
export function formaterDureeCourte(totalSecondes: number): string {
  const abs = Math.round(Math.abs(totalSecondes));
  const h = Math.floor(abs / 3600);
  const m = Math.round((abs % 3600) / 60);
  if (h === 0) return `${m} min`;
  return `${h} h ${m.toString().padStart(2, "0")} min`;
}

const PAS_GRADUATION_S = [5 * 60, 10 * 60, 15 * 60, 30 * 60, 3600, 2 * 3600, 3 * 3600, 6 * 3600];

/**
 * Pas de graduation (secondes) pour un axe horaire couvrant `dureeS` : le plus petit pas
 * « rond » (5 min, 15 min, 1 h...) qui ne dépasse pas `maxGraduations` — des graduations à
 * 09:00 / 09:15 plutôt que les 08:53 / 09:27 d'un découpage décimal en secondes.
 */
export function pasGraduationS(dureeS: number, maxGraduations = 10): number {
  const pas = PAS_GRADUATION_S.find((candidat) => dureeS / candidat <= maxGraduations);
  return pas ?? PAS_GRADUATION_S[PAS_GRADUATION_S.length - 1];
}

/**
 * Graduations « rondes » (secondes depuis minuit) d'un axe horaire borné à [debutS ; finS] :
 * les multiples du pas compris dans l'intervalle, bornes exclues si elles ne tombent pas rond.
 */
export function graduationsS(debutS: number, finS: number, maxGraduations = 10): number[] {
  const pas = pasGraduationS(finS - debutS, maxGraduations);
  const graduations: number[] = [];
  for (let t = Math.ceil(debutS / pas) * pas; t <= finS; t += pas) graduations.push(t);
  return graduations;
}
