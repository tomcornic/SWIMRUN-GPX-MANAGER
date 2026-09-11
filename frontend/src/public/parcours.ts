export type TypeTroncon = "run" | "swim";
export type TypePoi = "ravitaillement" | "entree_eau" | "sortie_eau" | "bouee";
export type CotePassage = "gauche" | "droite" | null;

export interface TronconParcours {
  numero: number;
  type: TypeTroncon;
  debutM: number;
  finM: number;
}

export interface PassageParcours {
  debutM: number;
  finM: number;
}

export interface GroupePassagesParcours {
  passages: PassageParcours[];
}

export interface CourseParcours {
  id: number;
  nom: string;
  couleur: string;
  troncons: TronconParcours[];
  passagesMultiples: GroupePassagesParcours[];
  trace: [number, number][]; // [lon, lat], ordre GeoJSON
  longueurTotaleM: number;
}

export interface PoiParcours {
  id: number;
  type: TypePoi;
  nom: string;
  description: string;
  lat: number;
  lon: number;
  cotePassage: CotePassage;
  distanceM: number;
}

export interface MetaEvenement {
  nom: string;
  date: string;
  courses: { id: number; nom: string; couleur: string }[];
  genereLe: string;
}

interface ApiTroncon {
  numero: number;
  type: TypeTroncon;
  debut_m: number;
  fin_m: number;
}

interface ApiPassage {
  debut_m: number;
  fin_m: number;
}

interface ApiGroupePassages {
  passages: ApiPassage[];
}

interface ApiCourseGeoJSON {
  properties: {
    id: number;
    nom: string;
    couleur: string;
    troncons: ApiTroncon[];
    passages_multiples: ApiGroupePassages[];
  };
  geometry: { type: "LineString"; coordinates: [number, number][] };
}

interface ApiPoi {
  id: number;
  type: TypePoi;
  nom: string;
  description: string;
  lat: number;
  lon: number;
  cote_passage: CotePassage;
  distance_m: number;
}

interface ApiMeta {
  nom: string;
  date: string;
  courses: { id: number; nom: string; couleur: string }[];
  genere_le: string;
}

export async function chargerMeta(): Promise<MetaEvenement | null> {
  const reponse = await fetch("/publie/meta.json");
  if (!reponse.ok) return null;
  const data = (await reponse.json()) as ApiMeta;
  return { nom: data.nom, date: data.date, courses: data.courses, genereLe: data.genere_le };
}

export function versCourseParcours(data: ApiCourseGeoJSON): CourseParcours {
  const troncons = data.properties.troncons.map((t) => ({
    numero: t.numero,
    type: t.type,
    debutM: t.debut_m,
    finM: t.fin_m,
  }));
  return {
    id: data.properties.id,
    nom: data.properties.nom,
    couleur: data.properties.couleur,
    troncons,
    passagesMultiples: data.properties.passages_multiples.map((groupe) => ({
      passages: groupe.passages.map((p) => ({ debutM: p.debut_m, finM: p.fin_m })),
    })),
    trace: data.geometry.coordinates,
    longueurTotaleM: troncons.at(-1)?.finM ?? 0,
  };
}

export function versPoiParcours(data: ApiPoi): PoiParcours {
  return {
    id: data.id,
    type: data.type,
    nom: data.nom,
    description: data.description,
    lat: data.lat,
    lon: data.lon,
    cotePassage: data.cote_passage,
    distanceM: data.distance_m,
  };
}

export async function chargerCourse(id: number, version: string): Promise<CourseParcours | null> {
  const reponse = await fetch(`/publie/course-${id}.geojson?v=${encodeURIComponent(version)}`);
  if (!reponse.ok) return null;
  return versCourseParcours((await reponse.json()) as ApiCourseGeoJSON);
}

export async function chargerPois(id: number, version: string): Promise<PoiParcours[]> {
  const reponse = await fetch(`/publie/pois-${id}.json?v=${encodeURIComponent(version)}`);
  if (!reponse.ok) return [];
  return ((await reponse.json()) as ApiPoi[]).map(versPoiParcours);
}
