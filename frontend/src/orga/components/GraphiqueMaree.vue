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
import { formaterHMS, graduationsS } from "../temps";

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

function cssVar(nom: string): string {
  // Lu sur <body>, pas <html> : les variables par thème sont posées sur [data-theme] au niveau body.
  return getComputedStyle(document.body).getPropertyValue(nom).trim();
}

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
        borderColor: cssVar("--couleur-swim"),
        backgroundColor: cssVar("--couleur-swim-fond"),
        fill: true,
        pointRadius: 0,
        borderWidth: 2,
        tension: 0.3,
      },
      {
        label: "PM / BM",
        data: maree.extremes.map((e) => ({ x: e.secondes, y: e.hauteurM })),
        borderColor: "transparent",
        backgroundColor: cssVar("--couleur-sable"),
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
      // Pas d'animation : un saut d'heure pendant l'animation d'apparition (1 s) laissait le
      // curseur à son ancienne position, l'animation en cours réécrivant sa cible initiale
      // par-dessus le `update("none")`. Le curseur est de toute façon redessiné à chaque image.
      animation: false,
      onClick: onClickGraphique,
      scales: {
        // Axe borné à la plage simulée (celle de l'horloge et de la série) : sans min/max,
        // Chart.js l'étire jusqu'aux pleines/basses mers saisies, souvent à plusieurs heures de
        // la course, et la courbe utile n'occupe plus qu'une fraction de la largeur.
        x: {
          type: "linear",
          min: horloge.borneDebutS,
          max: horloge.borneFinS,
          // Graduations imposées : avec min et max fixés, Chart.js n'applique pas `stepSize`
          // tel quel (il répartit les graduations entre les bornes : 08:55, 09:16...).
          afterBuildTicks: (axe) => {
            axe.ticks = graduationsS(axe.min, axe.max).map((value) => ({ value }));
          },
          ticks: {
            color: cssVar("--couleur-texte-att"),
            callback: (valeur) => formaterHMS(Number(valeur)).slice(0, 5),
          },
          grid: { color: cssVar("--couleur-bordure") },
        },
        y: {
          title: { display: true, text: "m", color: cssVar("--couleur-texte-att") },
          ticks: { color: cssVar("--couleur-texte-att") },
          grid: { color: cssVar("--couleur-bordure") },
        },
      },
      plugins: {
        legend: { labels: { color: cssVar("--couleur-texte") } },
        annotation: {
          annotations: {
            curseur: {
              type: "line",
              xMin: horloge.tempsS,
              xMax: horloge.tempsS,
              borderColor: cssVar("--couleur-curseur"),
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
  background: var(--couleur-surface);
  border-top: 1px solid var(--couleur-bordure);
  padding: 0.5rem 1rem;
}

.texte-hauteur {
  margin: 0 0 0.3rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--couleur-texte);
}

.conteneur-canvas {
  height: 140px;
}
</style>
