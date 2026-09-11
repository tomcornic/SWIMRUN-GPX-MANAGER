<script setup lang="ts">
import { onMounted, useTemplateRef } from "vue";

import { addCourseTrack, createSatelliteMap, type TrackFeature } from "../shared/map";

interface CourseSummary {
  id: number;
  name: string;
  color: string;
}

const mapContainer = useTemplateRef<HTMLDivElement>("mapContainer");

function readCourses(): CourseSummary[] {
  const el = document.getElementById("orga-courses");
  if (!el?.textContent) return [];
  try {
    return JSON.parse(el.textContent) as CourseSummary[];
  } catch {
    return [];
  }
}

onMounted(() => {
  if (!mapContainer.value) return;
  const map = createSatelliteMap(mapContainer.value);
  const courses = readCourses();

  map.on("load", () => {
    for (const course of courses) {
      fetch(`/orga/courses/${course.id}/trace.geojson`)
        .then((response) => (response.ok ? response.json() : null))
        .then((track: TrackFeature | null) => {
          if (track && track.geometry.coordinates.length > 0) {
            addCourseTrack(map, course.id, track, course.color);
          }
        })
        .catch(() => {
          // Tracé pas encore importé pour cette course : on l'ignore simplement.
        });
    }
  });
});
</script>

<template>
  <div ref="mapContainer" class="map-container"></div>
</template>
