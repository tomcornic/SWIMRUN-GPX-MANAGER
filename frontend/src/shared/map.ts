import { lineString } from "@turf/helpers";
import lineSliceAlong from "@turf/line-slice-along";
import type { Feature, LineString, Position } from "geojson";
import { AttributionControl, Map as MaplibreMap, NavigationControl, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

/**
 * maplibre-gl calcule l'URL de son worker à partir de `import.meta.url` du chunk où il est
 * bundlé (donc `.../assets/<notre-chunk>.js`) au lieu du fichier worker réel, qui n'est jamais
 * émis par Rollup — sans ce `setWorkerUrl`, le worker se charge en `text/html` (404) et toute la
 * carte reste inerte. Le chemin fixe correspond au fichier copié tel quel par le plugin Vite
 * `copyMaplibreWorkerFiles` (voir vite.config.ts) ; en dev, le worker se résout normalement
 * puisque Vite sert node_modules/maplibre-gl sans le fusionner dans un chunk.
 */
if (!import.meta.env.DEV) {
  setWorkerUrl("/static/dist/assets/maplibre-gl-worker.mjs");
}

const IGN_ORTHO_TILES_URL =
  "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0" +
  "&TILEMATRIXSET=PM_0_19&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal" +
  "&FORMAT=image/jpeg&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}";
const IGN_ATTRIBUTION = "&copy; IGN-F/Geoportail";

const OSM_PLAN_TILES_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const OSM_ATTRIBUTION = "&copy; OpenStreetMap contributors";

const SAINT_PABU_CENTER: [number, number] = [-4.596, 48.565];

export const ID_COUCHE_SATELLITE = "ign-ortho-layer";
export const ID_COUCHE_PLAN = "osm-plan-layer";
export type FondCarte = "satellite" | "plan";

/**
 * L'évènement "load" de maplibre-gl ne se déclenche qu'une fois dans toute la vie de la carte.
 * `map.loaded()` n'est PAS un indicateur fiable pour savoir s'il s'est déjà produit : cette
 * méthode redevient `false` dès que la carte recharge des tuiles en arrière-plan (zoom/pan),
 * bien après le premier chargement — s'y fier dans `surCarteChargee()` pouvait donc réabonner à
 * "load" alors que l'évènement était déjà passé depuis longtemps, et le callback n'était alors
 * plus jamais appelé (aucune erreur, juste plus rien ne s'affichait). On mémorise donc nous-mêmes,
 * une fois pour toutes, si "load" s'est déjà produit pour cette carte précise.
 */
const cartesChargees = new WeakSet<MaplibreMap>();

export function createSatelliteMap(container: HTMLElement): MaplibreMap {
  const map = new MaplibreMap({
    container,
    center: SAINT_PABU_CENTER,
    zoom: 13,
    style: {
      version: 8,
      sources: {
        "ign-ortho": {
          type: "raster",
          tiles: [IGN_ORTHO_TILES_URL],
          tileSize: 256,
          maxzoom: 19,
          attribution: IGN_ATTRIBUTION,
        },
        "osm-plan": {
          type: "raster",
          tiles: [OSM_PLAN_TILES_URL],
          tileSize: 256,
          maxzoom: 19,
          attribution: OSM_ATTRIBUTION,
        },
      },
      layers: [
        { id: ID_COUCHE_SATELLITE, type: "raster", source: "ign-ortho" },
        { id: ID_COUCHE_PLAN, type: "raster", source: "osm-plan", layout: { visibility: "none" } },
      ],
    },
  });

  map.addControl(new NavigationControl(), "top-right");
  map.addControl(new AttributionControl({ compact: true }), "bottom-right");
  map.once("load", () => cartesChargees.add(map));

  /**
   * Sur Safari/WebKit, le chargement asynchrone des polices auto-hébergées (fontsource, voir
   * CLAUDE.md P7) peut légèrement modifier la mise en page autour de la carte après le premier
   * rendu sans que le ResizeObserver interne de maplibre-gl ne redéclenche un resize à temps —
   * contrairement à Chrome/Firefox, où ça se corrige tout seul. Un `resize()` explicite à la
   * frame suivante et une fois les polices chargées corrige le canvas WebGL mal dimensionné
   * (rendu confiné à un petit coin du conteneur) sans dépendre de ce timing.
   */
  requestAnimationFrame(() => map.resize());
  void document.fonts?.ready?.then(() => map.resize());

  return map;
}

/**
 * À appeler pour exécuter `cb` une fois que la carte a fini son chargement initial — y compris
 * si on l'appelle après avoir attendu un fetch réseau (ex. `await coursesStore.charger(...)`)
 * pendant lequel "load" a déjà pu se produire (voir `cartesChargees` ci-dessus).
 */
export function surCarteChargee(map: MaplibreMap, cb: () => void): void {
  if (cartesChargees.has(map)) cb();
  else map.once("load", cb);
}

/** Commute entre le fond satellite (IGN) et le fond plan (OSM) — §6 : « commutateur vers une couche plan ». */
export function definirFondCarte(map: MaplibreMap, fond: FondCarte): void {
  map.setLayoutProperty(ID_COUCHE_SATELLITE, "visibility", fond === "satellite" ? "visible" : "none");
  map.setLayoutProperty(ID_COUCHE_PLAN, "visibility", fond === "plan" ? "visible" : "none");
}

export interface TronconBornes {
  type: "run" | "swim";
  debutM: number;
  finM: number;
}

export interface SegmentParType {
  type: "run" | "swim";
  coords: Position[];
}

/**
 * Découpe un tracé complet en segments par tronçon (via lineSliceAlong), pour un rendu
 * distinct course à pied / natation. Utilisé par l'orga (simulateur) et le site public.
 */
export function segmentsParType(ligne: Position[], troncons: TronconBornes[]): SegmentParType[] {
  if (ligne.length < 2) return [];
  const complet = lineString(ligne);
  return troncons.map((troncon) => {
    const tranche = lineSliceAlong(complet, troncon.debutM, troncon.finM, {
      units: "meters",
    }) as Feature<LineString>;
    return { type: troncon.type, coords: tranche.geometry.coordinates };
  });
}
