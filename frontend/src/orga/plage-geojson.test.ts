import { lineString } from "@turf/helpers";
import length from "@turf/length";
import { describe, expect, it } from "vitest";

import { geojsonPlage } from "./plage-geojson";

// ~1,1 km plein nord depuis Saint-Pabu, en 4 points.
const LIGNE = [
  [-4.596, 48.565],
  [-4.596, 48.568],
  [-4.596, 48.571],
  [-4.596, 48.575],
];

const VIDE = { type: "FeatureCollection", features: [] };

describe("geojsonPlage", () => {
  it("extrait la portion du tracé entre le dernier et le premier coureur", () => {
    const plage = geojsonPlage(LIGNE, 200, 700);
    expect(plage.type).toBe("Feature");
    expect(length(plage, { units: "meters" })).toBeCloseTo(500, 0);
  });

  it("renvoie une collection vide, sans lever d'exception, quand il n'y a rien à dessiner", () => {
    expect(geojsonPlage(LIGNE, null, null)).toEqual(VIDE); // course pas encore partie
    expect(geojsonPlage(LIGNE, 1100, 1100)).toEqual(VIDE); // tout le monde est arrivé
    expect(geojsonPlage(LIGNE, 0, 0)).toEqual(VIDE); // instant du départ
    expect(geojsonPlage([], 0, 100)).toEqual(VIDE); // course sans tracé
  });

  it("ne lève pas d'exception sur toute la durée d'une course, arrivée comprise", () => {
    const total = length(lineString(LIGNE), { units: "meters" });
    for (let queue = 0; queue <= total + 5; queue += 0.5) {
      const tete = Math.min(queue * 1.7, total);
      expect(() => geojsonPlage(LIGNE, Math.min(queue, total), tete)).not.toThrow();
    }
  });
});
