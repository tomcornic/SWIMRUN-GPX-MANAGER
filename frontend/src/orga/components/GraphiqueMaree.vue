<script setup lang="ts">
import type { ActiveElement, ChartEvent } from "chart.js";
import {
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import annotationPlugin from "chartjs-plugin-annotation";
import { computed, onMounted, onUnmounted, useTemplateRef, watch } from "vue";

import { useHorlogeStore } from "../stores/horloge";
import { useMareeStore } from "../stores/maree";
import { formaterHMS } from "../temps";

Chart.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  LineController,
  Tooltip,
  Legend,
  annotationPlugin
);

const canvasRef = useTemplateRef<HTMLCanvasElement>("canvasRef");
const horloge = useHorlogeStore();
const maree = useMareeStore();

let chart: Chart<"line"> | null = null;

const hauteurCourante = computed(() => maree.hauteurAt(horloge.tempsS));
const tendanceCourante = computed(() => maree.tendanceAt(horloge.tempsS));
const texteHauteur = computed(() => {
  if (hauteurCourante.value === null) return "Marée non configurée.";
  const hauteurFormatee = hauteurCourante.value.toFixed(2).replace(".", ",");
  const suffixeTendance = tendanceCourante.value ? ` — marée ${tendanceCourante.value}` : "";
  return `Hauteur d'eau : ${hauteurFormatee} m${suffixeTendance}`;
});

function construireDonnees() {
  return {
    datasets: [
      {
        label: "Hauteur d'eau (m)",
        data: maree.serie.map((p) => ({ x: p.secondes, y: p.hauteurM })),
        borderColor: "#0369a1",
        backgroundColor: "rgba(3, 105, 161, 0.12)",
        fill: true,
        pointRadius: 0,
        borderWidth: 2,
        tension: 0.3,
      },
      {
        label: "PM / BM",
        data: maree.extremes.map((e) => ({ x: e.secondes, y: e.hauteurM })),
        borderColor: "transparent",
        backgroundColor: "#f97316",
        pointRadius: 5,
        showLine: false,
      },
    ],
  };
}

function onClickGraphique(event: ChartEvent, _elements: ActiveElement[], chartInstance: Chart): void {
  const xScale = chartInstance.scales.x;
  if (!xScale || event.x === null) return;
  const secondes = xScale.getValueForPixel(event.x);
  if (secondes !== undefined) horloge.definirTemps(secondes);
}

function creerGraphique(): void {
  if (!canvasRef.value) return;
  chart = new Chart(canvasRef.value, {
    type: "line",
    data: construireDonnees(),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onClick: onClickGraphique,
      scales: {
        x: {
          type: "linear",
          ticks: { callback: (valeur) => formaterHMS(Number(valeur)).slice(0, 5) },
        },
        y: { title: { display: true, text: "m" } },
      },
      plugins: {
        annotation: {
          annotations: {
            curseur: {
              type: "line",
              xMin: horloge.tempsS,
              xMax: horloge.tempsS,
              borderColor: "#dc2626",
              borderWidth: 2,
            },
          },
        },
      },
    },
  });
}

watch(
  () => horloge.tempsS,
  (valeur) => {
    if (!chart) return;
    const annotations = chart.options.plugins?.annotation?.annotations;
    const curseur = (annotations as Record<string, { xMin: number; xMax: number }> | undefined)?.curseur;
    if (curseur) {
      curseur.xMin = valeur;
      curseur.xMax = valeur;
      chart.update("none");
    }
  }
);

watch(
  () => [maree.serie, maree.extremes],
  () => {
    if (!chart) return;
    chart.data = construireDonnees();
    chart.update();
  }
);

onMounted(creerGraphique);
onUnmounted(() => chart?.destroy());
</script>

<template>
  <div class="graphique-maree">
    <p class="texte-hauteur">{{ texteHauteur }}</p>
    <div class="conteneur-canvas">
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>

<style scoped>
.graphique-maree {
  background: white;
  border-top: 1px solid #e2e8f0;
  padding: 0.5rem 1rem;
}

.texte-hauteur {
  margin: 0 0 0.3rem;
  font-size: 0.9rem;
  font-weight: 600;
}

.conteneur-canvas {
  height: 140px;
}
</style>
