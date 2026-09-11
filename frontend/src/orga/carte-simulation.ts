import along from "@turf/along";
import { lineString, point } from "@turf/helpers";
import lineSliceAlong from "@turf/line-slice-along";
import type { Feature, Point, Position } from "geojson";
import { Map as MaplibreMap } from "maplibre-gl";
import type { CircleLayerSpecification, GeoJSONSource, LineLayerSpecification } from "maplibre-gl";

import { segmentsParType } from "../shared/map";
import type { Course } from "./simulation";

const EPAISSEUR_PLAGE = 8;

function sourceId(courseId: number, suffixe: string): string {
  return `course-${courseId}-${suffixe}`;
}

function setOrCreateSource(map: MaplibreMap, id: string, data: Feature): void {
  const existing = map.getSource(id) as GeoJSONSource | undefined;
  if (existing) {
    existing.setData(data);
  } else {
    map.addSource(id, { type: "geojson", data });
  }
}

/**
 * Affiche la plage d'une course (portion du tracé entre le dernier et le premier
 * coureur) comme une bande épaisse semi-transparente, extraite avec lineSliceAlong (§5).
 */
export function afficherPlage(
  map: MaplibreMap,
  courseId: number,
  ligne: Position[],
  couleur: string,
  debutM: number | null,
  finM: number | null
): void {
  const id = sourceId(courseId, "plage");
  const layerId = `${id}-line`;

  if (debutM === null || finM === null || ligne.length < 2 || finM <= debutM) {
    const source = map.getSource(id) as GeoJSONSource | undefined;
    source?.setData(lineString([]));
    return;
  }

  const complet = lineString(ligne);
  const tranche = lineSliceAlong(complet, debutM, finM, { units: "meters" });
  setOrCreateSource(map, id, tranche);

  if (!map.getLayer(layerId)) {
    const layer: LineLayerSpecification = {
      id: layerId,
      type: "line",
      source: id,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": couleur,
        "line-width": EPAISSEUR_PLAGE,
        "line-opacity": 0.55,
      },
    };
    map.addLayer(layer);
  }
}

function creerMarqueur(map: MaplibreMap, id: string, position: Feature<Point> | null, couleur: string): void {
  const layerId = `${id}-point`;
  setOrCreateSource(map, id, position ?? point([0, 0], {}, { id: "vide" }));

  if (!map.getLayer(layerId)) {
    const layer: CircleLayerSpecification = {
      id: layerId,
      type: "circle",
      source: id,
      paint: {
        "circle-radius": 6,
        "circle-color": couleur,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 2,
      },
    };
    map.addLayer(layer);
  }
  map.setLayoutProperty(layerId, "visibility", position ? "visible" : "none");
}

/** Place les marqueurs « tête » et « queue » de peloton sur le tracé, à leurs distances respectives. */
export function afficherMarqueurs(
  map: MaplibreMap,
  courseId: number,
  ligne: Position[],
  couleur: string,
  debutM: number | null,
  finM: number | null
): void {
  if (ligne.length < 2) return;
  const complet = lineString(ligne);

  const tete = finM === null ? null : along(complet, finM, { units: "meters" });
  const queue = debutM === null ? null : along(complet, debutM, { units: "meters" });

  creerMarqueur(map, sourceId(courseId, "tete"), tete, couleur);
  creerMarqueur(map, sourceId(courseId, "queue"), queue, "#ffffff");
}

/** Affiche le tracé de base avec les tronçons de natation en trait pointillé. */
export function afficherTraceDistincte(
  map: MaplibreMap,
  courseId: number,
  ligne: Position[],
  course: Course,
  couleur: string
): void {
  let cumul = 0;
  const bornes = course.troncons.map((troncon) => {
    const debutM = cumul;
    cumul += troncon.longueurM;
    return { type: troncon.type, debutM, finM: cumul };
  });
  const segments = segmentsParType(ligne, bornes);
  const runId = sourceId(courseId, "trace-run");
  const swimId = sourceId(courseId, "trace-swim");

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
      paint: { "line-color": couleur, "line-width": 3 },
    });
  }
  if (!map.getLayer(`${swimId}-line`)) {
    map.addLayer({
      id: `${swimId}-line`,
      type: "line",
      source: swimId,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": couleur, "line-width": 3, "line-dasharray": [1, 1.5] },
    });
  }
}
