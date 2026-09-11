import along from "@turf/along";
import { lineString } from "@turf/helpers";
import lineSliceAlong from "@turf/line-slice-along";
import type { Feature } from "geojson";
import { Marker } from "maplibre-gl";
import type { GeoJSONSource, Map as MaplibreMap } from "maplibre-gl";

import { segmentsParType } from "../shared/map";
import type { CourseParcours, PoiParcours } from "./parcours";

const ID_ICONE_FLECHE = "fleche-parcours";
const ARROW_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
  <path d="M4 12h13l-5-5m5 5l-5 5" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>`;

function sourceId(courseId: number, suffixe: string): string {
  return `parcours-${courseId}-${suffixe}`;
}

function setOrCreateSource(map: MaplibreMap, id: string, data: Feature): void {
  const existing = map.getSource(id) as GeoJSONSource | undefined;
  if (existing) {
    existing.setData(data);
  } else {
    map.addSource(id, { type: "geojson", data });
  }
}

/** Charge l'icône de flèche directionnelle (image, pas de police de glyphes nécessaire). */
export async function chargerIconeFleche(map: MaplibreMap): Promise<void> {
  if (map.hasImage(ID_ICONE_FLECHE)) return;
  const url = `data:image/svg+xml;base64,${btoa(ARROW_SVG)}`;
  const image = await map.loadImage(url);
  map.addImage(ID_ICONE_FLECHE, image.data);
}

/**
 * Trace de base : liseré blanc pour la lisibilité sur fond sombre, tronçons course/nage
 * distincts, flèches directionnelles régulièrement espacées (§6).
 */
export function afficherTrace(map: MaplibreMap, course: CourseParcours): void {
  const ligne = course.trace;
  if (ligne.length < 2) return;

  const haloId = sourceId(course.id, "halo");
  setOrCreateSource(map, haloId, lineString(ligne));
  if (!map.getLayer(`${haloId}-line`)) {
    map.addLayer({
      id: `${haloId}-line`,
      type: "line",
      source: haloId,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": "#ffffff", "line-width": 6, "line-opacity": 0.85 },
    });
  }

  const segments = segmentsParType(ligne, course.troncons);
  const runId = sourceId(course.id, "run");
  const swimId = sourceId(course.id, "swim");
  const versMultiLine = (type: "run" | "swim") =>
    ({
      type: "Feature" as const,
      properties: {},
      geometry: {
        type: "MultiLineString" as const,
        coordinates: segments.filter((s) => s.type === type).map((s) => s.coords),
      },
    }) satisfies Feature;

  setOrCreateSource(map, runId, versMultiLine("run"));
  setOrCreateSource(map, swimId, versMultiLine("swim"));

  if (!map.getLayer(`${runId}-line`)) {
    map.addLayer({
      id: `${runId}-line`,
      type: "line",
      source: runId,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": course.couleur, "line-width": 4 },
    });
  }
  if (!map.getLayer(`${swimId}-line`)) {
    map.addLayer({
      id: `${swimId}-line`,
      type: "line",
      source: swimId,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": course.couleur, "line-width": 4, "line-dasharray": [1, 1.5] },
    });
  }

  const flechesId = sourceId(course.id, "fleches");
  setOrCreateSource(map, flechesId, lineString(ligne));
  if (!map.getLayer(`${flechesId}-symbol`)) {
    map.addLayer({
      id: `${flechesId}-symbol`,
      type: "symbol",
      source: flechesId,
      layout: {
        "symbol-placement": "line",
        "symbol-spacing": 100,
        "icon-image": ID_ICONE_FLECHE,
        "icon-size": 0.8,
        "icon-allow-overlap": true,
        "icon-ignore-placement": true,
      },
    });
  }
}

/** Décale latéralement chaque passage d'une portion empruntée plusieurs fois (§6). */
export function afficherPassagesMultiples(map: MaplibreMap, course: CourseParcours): void {
  const ligne = course.trace;
  if (ligne.length < 2) return;
  const complet = lineString(ligne);

  course.passagesMultiples.forEach((groupe, groupeIndex) => {
    const nombrePassages = groupe.passages.length;
    groupe.passages.forEach((passage, passageIndex) => {
      const id = sourceId(course.id, `passage-${groupeIndex}-${passageIndex}`);
      const tranche = lineSliceAlong(complet, passage.debutM, passage.finM, { units: "meters" });
      setOrCreateSource(map, id, tranche);

      const decalage = (passageIndex - (nombrePassages - 1) / 2) * 5;
      if (!map.getLayer(`${id}-line`)) {
        map.addLayer({
          id: `${id}-line`,
          type: "line",
          source: id,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": course.couleur,
            "line-width": 4,
            "line-offset": decalage,
            "line-opacity": passageIndex % 2 === 0 ? 1 : 0.6,
          },
        });
      }
    });
  });
}

/** Pastilles numérotées « 1 »/« 2 » à l'entrée de chaque passage. */
export function afficherBadgesPassages(map: MaplibreMap, course: CourseParcours): Marker[] {
  const ligne = course.trace;
  if (ligne.length < 2) return [];
  const complet = lineString(ligne);
  const marqueurs: Marker[] = [];

  for (const groupe of course.passagesMultiples) {
    groupe.passages.forEach((passage, index) => {
      const point = along(complet, passage.debutM, { units: "meters" });
      const el = document.createElement("div");
      el.className = "badge-passage";
      el.textContent = String(index + 1);
      const marqueur = new Marker({ element: el })
        .setLngLat(point.geometry.coordinates as [number, number])
        .addTo(map);
      marqueurs.push(marqueur);
    });
  }

  return marqueurs;
}

const ICONES_POI: Record<PoiParcours["type"], string> = {
  ravitaillement: "🥤",
  entree_eau: "🏊",
  sortie_eau: "🚶",
  bouee: "🛟",
};

const LABELS_POI: Record<PoiParcours["type"], string> = {
  ravitaillement: "Ravitaillement",
  entree_eau: "Entrée dans l'eau",
  sortie_eau: "Sortie de l'eau",
  bouee: "Bouée directionnelle",
};

export { ICONES_POI, LABELS_POI };

/** Marqueurs POI cliquables, distincts par type (§6). */
export function afficherPois(
  map: MaplibreMap,
  pois: PoiParcours[],
  onClic: (poi: PoiParcours) => void
): Marker[] {
  return pois.map((poi) => {
    const el = document.createElement("button");
    el.type = "button";
    el.className = "marqueur-poi";
    el.textContent = ICONES_POI[poi.type];
    el.setAttribute("aria-label", `${LABELS_POI[poi.type]} : ${poi.nom}`);
    el.addEventListener("click", () => onClic(poi));
    return new Marker({ element: el }).setLngLat([poi.lon, poi.lat]).addTo(map);
  });
}

export function creerMarqueurPosition(map: MaplibreMap, couleur: string): Marker {
  const el = document.createElement("div");
  el.className = "marqueur-position";
  el.style.setProperty("--couleur-position", couleur);
  return new Marker({ element: el }).setLngLat([0, 0]).addTo(map);
}

function calquesDeCourse(map: MaplibreMap, courseId: number) {
  const prefix = sourceId(courseId, "");
  return (map.getStyle().layers ?? []).filter((layer) => layer.id.startsWith(prefix));
}

/** Masque tous les calques MapLibre d'une course (bascule d'onglet, §6). */
export function masquerCourse(map: MaplibreMap, courseId: number): void {
  for (const layer of calquesDeCourse(map, courseId)) {
    map.setLayoutProperty(layer.id, "visibility", "none");
  }
}

export function afficherCourseActive(map: MaplibreMap, courseId: number): void {
  for (const layer of calquesDeCourse(map, courseId)) {
    map.setLayoutProperty(layer.id, "visibility", "visible");
  }
}

/** Position (lon, lat) sur le tracé à une distance donnée, via turf.along (§6). */
export function positionSurTrace(course: CourseParcours, distanceM: number): [number, number] | null {
  if (course.trace.length < 2) return null;
  const complet = lineString(course.trace);
  const distanceClampee = Math.min(Math.max(distanceM, 0), course.longueurTotaleM);
  const point = along(complet, distanceClampee, { units: "meters" });
  return point.geometry.coordinates as [number, number];
}
