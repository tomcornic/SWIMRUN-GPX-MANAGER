<script setup lang="ts">
import { computed } from "vue";

import { useParcoursStore } from "../stores/parcours";

const store = useParcoursStore();

const longueurTotale = computed(() => store.courseActive?.longueurTotaleM ?? 0);

const segmentsBande = computed(() => {
  if (!store.courseActive || longueurTotale.value === 0) return [];
  return store.courseActive.troncons.map((t) => ({
    type: t.type,
    pourcentage: ((t.finM - t.debutM) / longueurTotale.value) * 100,
  }));
});

const reperesPoi = computed(() => {
  if (longueurTotale.value === 0) return [];
  return store.poisActifs.map((p) => ({
    id: p.id,
    pourcentage: (p.distanceM / longueurTotale.value) * 100,
  }));
});

function onInput(event: Event): void {
  store.definirDistance(Number((event.target as HTMLInputElement).value));
}
</script>

<template>
  <div v-if="store.courseActive" class="slider-km">
    <div class="bande" aria-hidden="true">
      <div
        v-for="(segment, index) in segmentsBande"
        :key="index"
        class="segment"
        :class="segment.type"
        :style="{ width: segment.pourcentage + '%' }"
      ></div>
      <div
        v-for="repere in reperesPoi"
        :key="repere.id"
        class="repere-poi"
        :style="{ left: repere.pourcentage + '%' }"
      ></div>
    </div>
    <input
      type="range"
      min="0"
      :max="longueurTotale"
      step="10"
      :value="store.distanceM"
      aria-label="Position sur le parcours, en mètres"
      @input="onInput"
    />
  </div>
</template>

<style scoped>
.slider-km {
  padding: 0.5rem 1rem;
  background: var(--couleur-surface);
}

.bande {
  position: relative;
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.3rem;
}

.segment.run {
  background: var(--couleur-run);
}

.segment.swim {
  background: var(--couleur-swim);
}

.repere-poi {
  position: absolute;
  top: -2px;
  width: 3px;
  height: 12px;
  background: var(--couleur-poi);
  transform: translateX(-50%);
}

input[type="range"] {
  width: 100%;
  height: 2rem;
}
</style>
