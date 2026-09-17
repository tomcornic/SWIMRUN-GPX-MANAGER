<script setup lang="ts">
import type { Map as MaplibreMap } from "maplibre-gl";
import { computed, onMounted, onUnmounted, useTemplateRef } from "vue";

import { createSatelliteMap, surCarteChargee } from "../shared/map";
import { afficherMarqueurs, afficherPlage, afficherTraceDistincte } from "./carte-simulation";
import ControlesLecture from "./components/ControlesLecture.vue";
import GraphiqueMaree from "./components/GraphiqueMaree.vue";
import PanneauCourse from "./components/PanneauCourse.vue";
import { plageAt } from "./simulation";
import { useCoursesStore } from "./stores/courses";
import { useHorlogeStore } from "./stores/horloge";
import { useMareeStore } from "./stores/maree";

const mapContainer = useTemplateRef<HTMLDivElement>("mapContainer");
const coursesStore = useCoursesStore();
const horloge = useHorlogeStore();
const mareeStore = useMareeStore();

const coursesAvecAllure = computed(() => coursesStore.courses.filter((c) => c.allure !== null));

function readCourseIds(): number[] {
  const el = document.getElementById("orga-courses");
  if (!el?.textContent) return [];
  try {
    const liste = JSON.parse(el.textContent) as { id: number }[];
    return liste.map((c) => c.id);
  } catch {
    return [];
  }
}

let map: MaplibreMap | null = null;
let frameId: number | null = null;
let dernierTimestamp: number | null = null;

function mettreAJourCarte(): void {
  if (!map) return;
  for (const course of coursesStore.courses) {
    if (!course.allure || course.traceCoordinates.length === 0) continue;
    const t = horloge.tempsS - course.departS;
    const plage = plageAt(course.course, course.allure, t);
    afficherPlage(map, course.id, course.traceCoordinates, course.couleur, plage.debutM, plage.finM);
    afficherMarqueurs(map, course.id, course.traceCoordinates, course.couleur, plage.debutM, plage.finM);
  }
}

function boucle(timestamp: number): void {
  try {
    if (dernierTimestamp !== null) {
      horloge.avancer((timestamp - dernierTimestamp) / 1000);
    }
    dernierTimestamp = timestamp;
    mettreAJourCarte();
  } catch (erreur) {
    // Une erreur ici ne doit jamais arrêter la boucle silencieusement : sans ce catch, une
    // exception dans mettreAJourCarte() empêche le requestAnimationFrame suivant d'être
    // planifié et la simulation entière se fige, sans que lecture/pause ne redonne rien.
    console.error("Erreur dans la boucle de simulation :", erreur);
  }
  frameId = requestAnimationFrame(boucle);
}

onMounted(async () => {
  if (!mapContainer.value) return;
  const carte = createSatelliteMap(mapContainer.value);
  map = carte;

  const ids = readCourseIds();
  await coursesStore.charger(ids);

  const bornes = coursesStore.bornesHorloge;
  horloge.initialiserBornes(bornes.debutS, bornes.finS);
  await mareeStore.charger(bornes.debutS, bornes.finS);

  surCarteChargee(carte, () => {
    for (const course of coursesStore.courses) {
      if (course.traceCoordinates.length === 0) continue;
      afficherTraceDistincte(carte, course.id, course.traceCoordinates, course.course, course.couleur);
    }
    mettreAJourCarte();
    frameId = requestAnimationFrame(boucle);
  });
});

onUnmounted(() => {
  if (frameId !== null) cancelAnimationFrame(frameId);
});
</script>

<template>
  <div class="app-layout">
    <div class="app-body">
      <div ref="mapContainer" class="map-container"></div>
      <aside v-if="coursesAvecAllure.length" class="panneau-lateral">
        <PanneauCourse
          v-for="c in coursesAvecAllure"
          :key="c.id"
          :course="c"
          :temps-global-s="horloge.tempsS"
        />
      </aside>
    </div>
    <GraphiqueMaree v-if="coursesAvecAllure.length && mareeStore.serie.length" />
    <ControlesLecture v-if="coursesAvecAllure.length" />
    <p v-else class="aucune-simulation">
      Aucune course avec des allures configurées : ouvrez « Courses » pour les saisir.
    </p>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.app-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.panneau-lateral {
  width: 260px;
  flex-shrink: 0;
  overflow-y: auto;
  padding: 0.75rem;
  background: var(--couleur-surface);
  border-left: 1px solid var(--couleur-bordure);
}

.aucune-simulation {
  margin: 0;
  padding: 0.6rem 1rem;
  background: var(--couleur-alerte-fond);
  color: var(--couleur-alerte-texte);
  font-size: 0.85rem;
}
</style>
