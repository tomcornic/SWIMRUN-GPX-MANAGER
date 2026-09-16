<script setup lang="ts">
import type { Map as MaplibreMap, Marker } from "maplibre-gl";
import { onMounted, onUnmounted, ref, useTemplateRef, watch } from "vue";

import { createSatelliteMap, definirFondCarte, type FondCarte } from "../shared/map";
import {
  afficherBadgesPassages,
  afficherCourseActive,
  afficherPassagesMultiples,
  afficherPois,
  afficherTrace,
  chargerIconeFleche,
  creerMarqueurPosition,
  masquerCourse,
  positionSurTrace,
} from "./carte-parcours";
import EncartInfo from "./components/EncartInfo.vue";
import LegendeParcours from "./components/LegendeParcours.vue";
import PanneauPoi from "./components/PanneauPoi.vue";
import SelecteurCourse from "./components/SelecteurCourse.vue";
import SliderKm from "./components/SliderKm.vue";
import type { PoiParcours } from "./parcours";
import { useParcoursStore } from "./stores/parcours";

const mapContainer = useTemplateRef<HTMLDivElement>("mapContainer");
const store = useParcoursStore();

const poiSelectionne = ref<PoiParcours | null>(null);
const suivreCurseur = ref(true);
const enLectureAuto = ref(false);
const fond = ref<FondCarte>("satellite");

const VITESSE_LECTURE_M_PAR_S = 15;

let map: MaplibreMap | null = null;
let marqueurPosition: Marker | null = null;
let markersParCourse = new Map<number, Marker[]>();
let coursesRendues = new Set<number>();
let frameId: number | null = null;
let dernierTimestamp: number | null = null;

function afficherMarqueursDe(courseId: number, visible: boolean): void {
  for (const marqueur of markersParCourse.get(courseId) ?? []) {
    marqueur.getElement().style.display = visible ? "" : "none";
  }
}

function rendreCourse(carte: MaplibreMap, courseId: number): void {
  const course = store.courses[courseId];
  if (!course) return;

  afficherTrace(carte, course);
  afficherPassagesMultiples(carte, course);

  const badges = afficherBadgesPassages(carte, course);
  const pois = afficherPois(carte, store.pois[courseId] ?? [], (poi) => {
    poiSelectionne.value = poi;
  });
  markersParCourse.set(courseId, [...badges, ...pois]);
  coursesRendues.add(courseId);
}

function synchroniserCourseActive(previousId: number | null, courseId: number | null): void {
  if (!map || courseId === null) return;

  if (previousId !== null && previousId !== courseId) {
    masquerCourse(map, previousId);
    afficherMarqueursDe(previousId, false);
  }

  if (!coursesRendues.has(courseId)) {
    rendreCourse(map, courseId);
  } else {
    afficherCourseActive(map, courseId);
    afficherMarqueursDe(courseId, true);
  }
}

function mettreAJourPosition(): void {
  const course = store.courseActive;
  if (!map || !marqueurPosition || !course) return;

  const position = positionSurTrace(course, store.distanceM);
  if (!position) return;

  marqueurPosition.setLngLat(position);
  if (suivreCurseur.value) {
    map.easeTo({ center: position, duration: 200 });
  }
}

function boucleLecture(timestamp: number): void {
  if (enLectureAuto.value && dernierTimestamp !== null) {
    const deltaS = (timestamp - dernierTimestamp) / 1000;
    const total = store.courseActive?.longueurTotaleM ?? 0;
    const nouvelle = store.distanceM + deltaS * VITESSE_LECTURE_M_PAR_S;
    store.definirDistance(nouvelle);
    if (nouvelle >= total) enLectureAuto.value = false;
  }
  dernierTimestamp = timestamp;
  frameId = requestAnimationFrame(boucleLecture);
}

function allerAuPoi(distanceM: number): void {
  store.definirDistance(distanceM);
  poiSelectionne.value = null;
}

function basculerFond(): void {
  fond.value = fond.value === "satellite" ? "plan" : "satellite";
  if (map) definirFondCarte(map, fond.value);
}

watch(
  () => store.courseActiveId,
  (courseId, previousId) => synchroniserCourseActive(previousId ?? null, courseId)
);

watch(() => store.distanceM, mettreAJourPosition);

onMounted(async () => {
  if (!mapContainer.value) return;
  const carte = createSatelliteMap(mapContainer.value);
  map = carte;

  await store.initialiser();

  carte.on("load", async () => {
    await chargerIconeFleche(carte);
    marqueurPosition = creerMarqueurPosition(carte, store.courseActive?.couleur ?? "#1d4ed8");

    if (store.courseActiveId !== null) {
      synchroniserCourseActive(null, store.courseActiveId);
      const trace = store.courseActive?.trace;
      if (trace && trace.length > 0) {
        carte.setCenter(trace[0]);
      }
      mettreAJourPosition();
    }

    dernierTimestamp = performance.now();
    frameId = requestAnimationFrame(boucleLecture);
  });
});

onUnmounted(() => {
  if (frameId !== null) cancelAnimationFrame(frameId);
  for (const marqueurs of markersParCourse.values()) {
    for (const marqueur of marqueurs) marqueur.remove();
  }
});
</script>

<template>
  <div class="app-parcours">
    <SelecteurCourse />
    <div class="zone-carte">
      <div ref="mapContainer" class="carte"></div>
      <button type="button" class="bouton-fond" @click="basculerFond">
        {{ fond === "satellite" ? "Vue plan" : "Vue satellite" }}
      </button>
      <button
        type="button"
        class="bouton-suivre"
        :class="{ actif: suivreCurseur }"
        @click="suivreCurseur = !suivreCurseur"
      >
        {{ suivreCurseur ? "Suivi activé" : "Suivi désactivé" }}
      </button>
      <button type="button" class="bouton-lecture" @click="enLectureAuto = !enLectureAuto">
        {{ enLectureAuto ? "⏸" : "▶" }}
      </button>
      <PanneauPoi :poi="poiSelectionne" @fermer="poiSelectionne = null" @aller="allerAuPoi" />
    </div>
    <SliderKm />
    <EncartInfo />
    <LegendeParcours />
  </div>
</template>

<style scoped>
.app-parcours {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.zone-carte {
  position: relative;
  flex: 1;
  min-height: 0;
}

.carte {
  width: 100%;
  height: 100%;
}

.bouton-fond,
.bouton-suivre,
.bouton-lecture {
  position: absolute;
  padding: 0.4rem 0.7rem;
  border: none;
  border-radius: 6px;
  background: var(--couleur-chrome-fond-survol);
  color: var(--couleur-chrome-texte);
  font: inherit;
  font-size: 0.8rem;
  cursor: pointer;
  z-index: 5;
}

.bouton-fond {
  top: 0.6rem;
  left: 0.6rem;
}

.bouton-suivre {
  top: 0.6rem;
  left: 6.5rem;
}

.bouton-suivre.actif {
  background: var(--couleur-accent);
  color: var(--couleur-accent-texte);
}

.bouton-lecture {
  bottom: 0.6rem;
  left: 0.6rem;
  font-size: 1.1rem;
  padding: 0.4rem 0.8rem;
}
</style>
