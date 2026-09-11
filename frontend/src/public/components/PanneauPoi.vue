<script setup lang="ts">
import { LABELS_POI } from "../carte-parcours";
import type { PoiParcours } from "../parcours";

defineProps<{ poi: PoiParcours | null }>();
const emit = defineEmits<{ fermer: []; aller: [distanceM: number] }>();
</script>

<template>
  <div v-if="poi" class="panneau-poi" role="dialog" :aria-label="poi.nom">
    <button type="button" class="fermer" aria-label="Fermer" @click="emit('fermer')">✕</button>
    <h3>{{ poi.nom }}</h3>
    <p class="type">{{ LABELS_POI[poi.type] }} — {{ (poi.distanceM / 1000).toFixed(2) }} km</p>
    <p v-if="poi.description">{{ poi.description }}</p>
    <p v-if="poi.cotePassage">À laisser à {{ poi.cotePassage === "gauche" ? "gauche" : "droite" }}.</p>
    <button type="button" class="aller" @click="emit('aller', poi.distanceM)">Aller à ce point</button>
  </div>
</template>

<style scoped>
.panneau-poi {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: white;
  padding: 1rem;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.2);
  z-index: 20;
}

@media (min-width: 720px) {
  .panneau-poi {
    left: auto;
    right: 1rem;
    bottom: 6rem;
    width: 300px;
    border-radius: 12px;
  }
}

.fermer {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  border: none;
  background: none;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.3rem;
}

h3 {
  margin: 0 0 0.3rem;
  padding-right: 1.5rem;
}

.type {
  color: #64748b;
  font-size: 0.85rem;
  margin: 0 0 0.5rem;
}

.aller {
  margin-top: 0.6rem;
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 6px;
  background: #1d4ed8;
  color: white;
  cursor: pointer;
  font: inherit;
}
</style>
