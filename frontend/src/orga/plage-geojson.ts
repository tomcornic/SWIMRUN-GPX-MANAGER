import { featureCollection, lineString } from "@turf/helpers";
import lineSliceAlong from "@turf/line-slice-along";
import type { Feature, FeatureCollection, LineString, Position } from "geojson";

/**
 * GeoJSON de la plage d'une course (portion du tracé entre le dernier et le premier coureur,
 * extraite avec lineSliceAlong — §5). Quand il n'y a rien à dessiner (course pas partie, tout le
 * monde arrivé, tracé trop court), renvoie une collection vide : surtout pas `lineString([])`,
 * que Turf refuse en levant une exception (« coordinates must be an array of two or more
 * positions ») — appelée à chaque image, elle figeait les marqueurs de la course et de toutes
 * les suivantes dès que le dernier coureur franchissait l'arrivée.
 */
export function geojsonPlage(
  ligne: Position[],
  debutM: number | null,
  finM: number | null
): Feature<LineString> | FeatureCollection {
  if (debutM === null || finM === null || ligne.length < 2 || finM <= debutM) {
    return featureCollection([]);
  }
  return lineSliceAlong(lineString(ligne), debutM, finM, { units: "meters" });
}
