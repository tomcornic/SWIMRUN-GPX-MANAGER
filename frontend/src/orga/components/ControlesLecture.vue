<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";

import { useHorlogeStore, VITESSES, type Vitesse } from "../stores/horloge";
import { formaterHMS, heureVersSecondes } from "../temps";

const horloge = useHorlogeStore();

const heureAffichee = computed(() => formaterHMS(horloge.tempsS));

function onSliderInput(event: Event): void {
  horloge.definirTemps(Number((event.target as HTMLInputElement).value));
}

function onChangerVitesse(event: Event): void {
  horloge.definirVitesse(Number((event.target as HTMLSelectElement).value) as Vitesse);
}

function onSaisieHeure(event: Event): void {
  const valeur = (event.target as HTMLInputElement).value;
  if (!valeur) return;
  horloge.definirTemps(heureVersSecondes(valeur));
}

function onKeydown(event: KeyboardEvent): void {
  const cible = event.target as HTMLElement | null;
  if (event.code === "Space" && cible?.tagName !== "INPUT" && cible?.tagName !== "SELECT") {
    event.preventDefault();
    horloge.basculerLecture();
  }
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onUnmounted(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <div class="controles-lecture">
    <button type="button" class="bouton-lecture" @click="horloge.basculerLecture()">
      {{ horloge.enLecture ? "⏸ Pause" : "▶ Lecture" }}
    </button>

    <select :value="horloge.vitesse" @change="onChangerVitesse">
      <option v-for="v in VITESSES" :key="v" :value="v">×{{ v }}</option>
    </select>

    <span class="horloge">{{ heureAffichee }}</span>

    <label class="saut-heure">
      Aller à :
      <input type="time" step="1" @change="onSaisieHeure" title="Aller à une heure précise" />
    </label>

    <input
      class="slider"
      type="range"
      :min="horloge.borneDebutS"
      :max="horloge.borneFinS"
      :value="horloge.tempsS"
      step="10"
      @input="onSliderInput"
    />
  </div>
</template>

<style scoped>
.controles-lecture {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  background: var(--couleur-chrome-fond);
  color: var(--couleur-chrome-texte);
}

.bouton-lecture {
  padding: 0.4rem 0.9rem;
  border: none;
  border-radius: 4px;
  background: var(--couleur-accent);
  color: var(--couleur-accent-texte);
  cursor: pointer;
  font: inherit;
  white-space: nowrap;
}

.horloge {
  font-variant-numeric: tabular-nums;
  font-size: 1.1rem;
  min-width: 5.5rem;
}

.slider {
  flex: 1;
  min-width: 8rem;
}

select,
input[type="time"] {
  font: inherit;
}

.saut-heure {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  white-space: nowrap;
}
</style>
