<script setup lang="ts">
import { computed } from "vue";

import { ICONES_POI, LABELS_POI } from "../carte-parcours";
import { useParcoursStore } from "../stores/parcours";

const store = useParcoursStore();
const aDesPassagesMultiples = computed(() => (store.courseActive?.passagesMultiples.length ?? 0) > 0);
</script>

<template>
  <details class="legende">
    <summary>Légende</summary>
    <ul>
      <li><span class="ligne run" aria-hidden="true"></span> Course à pied</li>
      <li><span class="ligne swim" aria-hidden="true"></span> Natation</li>
      <li v-if="aDesPassagesMultiples">Portion empruntée plusieurs fois — passages décalés et numérotés</li>
      <li v-for="(label, type) in LABELS_POI" :key="type">{{ ICONES_POI[type] }} {{ label }}</li>
    </ul>
  </details>
</template>

<style scoped>
.legende {
  padding: 0.4rem 1rem;
  background: white;
  font-size: 0.8rem;
  border-top: 1px solid #e2e8f0;
}

summary {
  cursor: pointer;
  font-weight: 600;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0.4rem 0 0;
}

li {
  margin: 0.15rem 0;
}

.ligne {
  display: inline-block;
  width: 20px;
  height: 3px;
  margin-right: 0.3rem;
  vertical-align: middle;
}

.ligne.run {
  background: #16a34a;
}

.ligne.swim {
  background: #0284c7;
}
</style>
