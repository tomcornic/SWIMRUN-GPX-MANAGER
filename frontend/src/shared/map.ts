import { AttributionControl, Map as MaplibreMap, NavigationControl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const IGN_ORTHO_TILES_URL =
  "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0" +
  "&TILEMATRIXSET=PM_0_19&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal" +
  "&FORMAT=image/jpeg&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}";

const IGN_ATTRIBUTION = "&copy; IGN-F/Geoportail";

const SAINT_PABU_CENTER: [number, number] = [-4.596, 48.565];

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
      },
      layers: [
        {
          id: "ign-ortho-layer",
          type: "raster",
          source: "ign-ortho",
        },
      ],
    },
  });

  map.addControl(new NavigationControl(), "top-right");
  map.addControl(new AttributionControl({ compact: true }), "bottom-right");

  return map;
}
