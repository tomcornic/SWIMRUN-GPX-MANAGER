<script setup lang="ts">
import { computed } from "vue";

import { messagePassage, passageActifA, prochainPoi, tronconALaDistance } from "../navigation";
import { useParcoursStore } from "../stores/parcours";

const store = useParcoursStore();

const LABEL_TYPE = { run: "Course à pied", swim: "Natation" } as const;

const position = computed(() => {
  const course = store.courseActive;
  return course ? tronconALaDistance(course, store.distanceM) : null;
});

const passage = computed(() => {
  const course = store.courseActive;
  return course ? passageActifA(course.passagesMultiples, store.distanceM) : null;
});

const suivant = computed(() => prochainPoi(store.poisActifs, store.distanceM));
</script>

<template>
  <div v-if="store.courseActive" class="encart-info">
    <p class="km">{{ (store.distanceM / 1000).toFixed(2) }} km</p>
    <p v-if="position">
      Tronçon {{ position.index + 1 }} / {{ position.total }} — {{ LABEL_TYPE[position.troncon.type] }}
      ({{ Math.round(position.distanceRestanteM) }} m restants)
    </p>
    <p v-if="passage" class="message-passage">{{ messagePassage(passage) }}</p>
    <p v-if="suivant">Prochain POI : {{ suivant.poi.nom }} — dans {{ Math.round(suivant.distanceM) }} m</p>
  </div>
</template>

<style scoped>
.encart-info {
  padding: 0.5rem 1rem;
  background: white;
  border-top: 1px solid #e2e8f0;
  font-size: 0.9rem;
}

.km {
  font-size: 1.3rem;
  font-weight: 700;
  margin: 0 0 0.2rem;
}

.message-passage {
  color: #b45309;
  font-weight: 600;
}

p {
  margin: 0.15rem 0;
}
</style>
