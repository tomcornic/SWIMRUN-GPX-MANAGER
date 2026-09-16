<script setup lang="ts">
import { useParcoursStore } from "../stores/parcours";

const store = useParcoursStore();
</script>

<template>
  <nav
    v-if="store.meta && store.meta.courses.length > 1"
    class="selecteur-course"
    role="tablist"
    aria-label="Choix de la course"
  >
    <button
      v-for="course in store.meta.courses"
      :key="course.id"
      type="button"
      role="tab"
      :aria-selected="course.id === store.courseActiveId"
      :class="{ actif: course.id === store.courseActiveId }"
      :style="{ '--couleur': course.couleur }"
      @click="store.selectionnerCourse(course.id)"
    >
      {{ course.nom }}
    </button>
  </nav>
</template>

<style scoped>
.selecteur-course {
  display: flex;
  gap: 0.4rem;
  padding: 0.5rem;
  overflow-x: auto;
  background: var(--couleur-chrome-fond);
}

.selecteur-course button {
  border: none;
  border-radius: 999px;
  padding: 0.4rem 0.9rem;
  background: var(--couleur-chrome-fond-clair);
  color: var(--couleur-chrome-texte);
  font: inherit;
  cursor: pointer;
  white-space: nowrap;
  border-bottom: 3px solid transparent;
}

.selecteur-course button.actif {
  border-bottom-color: var(--couleur);
  background: var(--couleur-chrome-fond-actif);
  font-weight: 600;
}
</style>
