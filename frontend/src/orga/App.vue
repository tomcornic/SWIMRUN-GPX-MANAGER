<script setup lang="ts">
import { onMounted, useTemplateRef } from "vue";

import { createSatelliteMap } from "../shared/map";

const mapContainer = useTemplateRef<HTMLDivElement>("mapContainer");

onMounted(() => {
  if (mapContainer.value) {
    createSatelliteMap(mapContainer.value);
  }
});
</script>

<template>
  <div ref="mapContainer" class="map-container"></div>
</template>
