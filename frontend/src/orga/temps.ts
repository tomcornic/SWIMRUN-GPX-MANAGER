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
