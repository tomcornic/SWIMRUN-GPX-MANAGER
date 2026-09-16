<script setup lang="ts">
import { Marker } from "maplibre-gl";
import type { MapMouseEvent } from "maplibre-gl";
import { onMounted, useTemplateRef } from "vue";

import { createSatelliteMap } from "../../shared/map";

const props = defineProps<{
  latInputId: string;
  lonInputId: string;
  latInitial?: number;
  lonInitial?: number;
}>();

const mapContainer = useTemplateRef<HTMLDivElement>("mapContainer");

function ecrireCoordonnees(lat: number, lon: number): void {
  const latInput = document.getElementById(props.latInputId) as HTMLInputElement | null;
  const lonInput = document.getElementById(props.lonInputId) as HTMLInputElement | null;
  if (latInput) latInput.value = lat.toFixed(6);
  if (lonInput) lonInput.value = lon.toFixed(6);
}

onMounted(() => {
  if (!mapContainer.value) return;
  const map = createSatelliteMap(mapContainer.value);

  let marker: Marker | null = null;
  if (props.latInitial !== undefined && props.lonInitial !== undefined) {
    marker = new Marker({ draggable: true })
      .setLngLat([props.lonInitial, props.latInitial])
      .addTo(map);
    marker.on("dragend", () => {
      const { lat, lng } = marker!.getLngLat();
      ecrireCoordonnees(lat, lng);
    });
    map.setCenter([props.lonInitial, props.latInitial]);
  }

  map.on("click", (evenement: MapMouseEvent) => {
    const { lat, lng } = evenement.lngLat;
    ecrireCoordonnees(lat, lng);
    if (marker) {
      marker.setLngLat([lng, lat]);
    } else {
      marker = new Marker({ draggable: true }).setLngLat([lng, lat]).addTo(map);
      marker.on("dragend", () => {
        const { lat: dragLat, lng: dragLng } = marker!.getLngLat();
        ecrireCoordonnees(dragLat, dragLng);
      });
    }
  });
});
</script>

<template>
  <div class="conteneur-carte-poi">
    <div ref="mapContainer" class="carte-poi"></div>
    <p class="aide">Cliquez sur la carte pour placer le POI (marqueur déplaçable).</p>
  </div>
</template>

<style scoped>
.conteneur-carte-poi {
  margin: 0.75rem 0;
}

.carte-poi {
  height: 320px;
  border: 1px solid var(--couleur-bordure);
}

.aide {
  font-size: 0.8rem;
  color: var(--couleur-texte-att);
  margin: 0.3rem 0 0;
}
</style>
