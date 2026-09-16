<script setup lang="ts">
import { lineString } from "@turf/helpers";
import length from "@turf/length";
import nearestPointOnLine from "@turf/nearest-point-on-line";
import type { Feature, LineString, Position } from "geojson";
import type { Map as MaplibreMap, MapMouseEvent } from "maplibre-gl";
import { Marker } from "maplibre-gl";
import { onMounted, ref, useTemplateRef, watch } from "vue";

import { createSatelliteMap } from "../../shared/map";

const props = defineProps<{
  sourceUrl: string;
  hiddenInputId: string;
}>();

const mapContainer = useTemplateRef<HTMLDivElement>("mapContainer");

interface Coupure {
  id: number;
  distanceM: number;
  lngLat: [number, number];
}

const coupures = ref<Coupure[]>([]);
const types = ref<string[]>(["run"]);
const totalDistanceM = ref(0);
const chargee = ref(false);

let ligneTurf: Feature<LineString> | null = null;
let prochainId = 1;
let map: MaplibreMap | null = null;
let markers: Marker[] = [];

function debutSegment(index: number): number {
  return index === 0 ? 0 : coupures.value[index - 1].distanceM;
}

function finSegment(index: number): number {
  return index === coupures.value.length ? totalDistanceM.value : coupures.value[index].distanceM;
}

function formatDistance(metres: number): string {
  return `${(metres / 1000).toFixed(2)} km`;
}

function calculerBounds(coords: Position[]): [[number, number], [number, number]] {
  let [minLng, minLat] = coords[0];
  let [maxLng, maxLat] = coords[0];
  for (const [lng, lat] of coords) {
    minLng = Math.min(minLng, lng);
    minLat = Math.min(minLat, lat);
    maxLng = Math.max(maxLng, lng);
    maxLat = Math.max(maxLat, lat);
  }
  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}

// Le nombre de segments (= coupures + 1) change à chaque ajout/suppression de coupure : on
// réinitialise alors les types en alternant course/natation par défaut (simple point de départ
// à ajuster à la main), plutôt que de deviner — voir la décision « approche purement manuelle »
// dans CLAUDE.md.
watch(
  () => coupures.value.length,
  (n) => {
    types.value = Array.from({ length: n + 1 }, (_, i) => (i % 2 === 0 ? "run" : "swim"));
  },
  { immediate: true }
);

watch(
  [coupures, types],
  () => {
    const input = document.getElementById(props.hiddenInputId) as HTMLInputElement | null;
    if (!input) return;
    input.value = JSON.stringify({
      cuts_m: coupures.value.map((c) => c.distanceM),
      types: types.value,
    });
  },
  { deep: true, immediate: true }
);

function snapper(lngLat: [number, number]): { distanceM: number; lngLat: [number, number] } {
  const proche = nearestPointOnLine(ligneTurf!, lngLat, { units: "meters" });
  const [lng, lat] = proche.geometry.coordinates;
  return { distanceM: proche.properties.totalDistance, lngLat: [lng, lat] };
}

function ajouterCoupure(lngLat: [number, number]): void {
  if (!ligneTurf) return;
  const { distanceM, lngLat: snappe } = snapper(lngLat);
  coupures.value = [...coupures.value, { id: prochainId++, distanceM, lngLat: snappe }].sort(
    (a, b) => a.distanceM - b.distanceM
  );
}

function supprimerCoupure(id: number): void {
  coupures.value = coupures.value.filter((c) => c.id !== id);
}

function deplacerCoupure(id: number, lngLat: [number, number]): void {
  if (!ligneTurf) return;
  const { distanceM, lngLat: snappe } = snapper(lngLat);
  coupures.value = coupures.value
    .map((c) => (c.id === id ? { ...c, distanceM, lngLat: snappe } : c))
    .sort((a, b) => a.distanceM - b.distanceM);
}

function redessinerMarqueurs(): void {
  if (!map) return;
  for (const marker of markers) marker.remove();
  markers = coupures.value.map((coupure) => {
    const marker = new Marker({ draggable: true, color: "#d94f72" }).setLngLat(coupure.lngLat).addTo(map!);
    marker.on("drag", () => {
      const { lat, lng } = marker.getLngLat();
      deplacerCoupure(coupure.id, [lng, lat]);
    });
    return marker;
  });
}

watch(coupures, redessinerMarqueurs, { deep: true });

onMounted(async () => {
  if (!mapContainer.value) return;
  const carte = createSatelliteMap(mapContainer.value);
  map = carte;

  const reponse = await fetch(props.sourceUrl);
  const geojson = (await reponse.json()) as Feature<LineString>;
  const coords = geojson.geometry.coordinates;
  ligneTurf = lineString(coords);
  totalDistanceM.value = length(ligneTurf, { units: "meters" });
  chargee.value = true;

  carte.on("load", () => {
    carte.addSource("decoupage-trace", { type: "geojson", data: geojson });
    carte.addLayer({
      id: "decoupage-trace-line",
      type: "line",
      source: "decoupage-trace",
      paint: { "line-color": "#3f6d90", "line-width": 4 },
    });
    carte.fitBounds(calculerBounds(coords), { padding: 40, duration: 0 });
  });

  carte.on("click", (evenement: MapMouseEvent) => {
    ajouterCoupure([evenement.lngLat.lng, evenement.lngLat.lat]);
  });
});
</script>

<template>
  <div class="decoupage-picker">
    <div ref="mapContainer" class="decoupage-carte"></div>
    <div class="decoupage-panneau">
      <p v-if="!chargee" class="aide">Chargement du tracé…</p>
      <template v-else>
        <p class="aide">
          Cliquez sur le tracé pour ajouter un point de coupure (glissable). {{ coupures.length }}
          coupure(s), {{ types.length }} segment(s) sur {{ formatDistance(totalDistanceM) }} au total.
        </p>
        <ol class="liste-segments">
          <li v-for="(_, index) in types" :key="index" class="segment-item">
            <span class="segment-label">
              Segment {{ index + 1 }} — {{ formatDistance(debutSegment(index)) }} →
              {{ formatDistance(finSegment(index)) }}
            </span>
            <select v-model="types[index]">
              <option value="run">Course à pied</option>
              <option value="swim">Natation</option>
            </select>
            <button
              v-if="index < coupures.length"
              type="button"
              class="btn-danger"
              @click="supprimerCoupure(coupures[index].id)"
            >
              Supprimer la coupure suivante
            </button>
          </li>
        </ol>
      </template>
    </div>
  </div>
</template>

<style scoped>
.decoupage-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin: 0.75rem 0;
}

.decoupage-carte {
  flex: 2 1 480px;
  height: 480px;
  border: 1px solid var(--couleur-bordure);
}

.decoupage-panneau {
  flex: 1 1 280px;
  min-width: 260px;
}

.aide {
  font-size: 0.85rem;
  color: var(--couleur-texte-att);
  margin: 0 0 0.5rem;
}

.liste-segments {
  list-style: none;
  margin: 0;
  padding: 0;
}

.segment-item {
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: var(--couleur-surface-alt);
  border-left: 3px solid var(--couleur-accent);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.segment-label {
  font-size: 0.85rem;
  flex: 1 1 100%;
}

.segment-item select {
  font: inherit;
}

.btn-danger {
  border: none;
  border-radius: 4px;
  padding: 0.3rem 0.6rem;
  background: var(--couleur-danger);
  color: white;
  cursor: pointer;
  font-size: 0.8rem;
}
</style>
