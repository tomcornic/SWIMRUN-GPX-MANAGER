<script setup lang="ts">
import { computed } from "vue";

import { distanceAt, etatCoureur, tronconActuel } from "../simulation";
import type { CourseSimulation } from "../stores/courses";
import { formaterDureeCourte } from "../temps";

const props = defineProps<{
  course: CourseSimulation;
  tempsGlobalS: number;
}>();

const tempsCourseS = computed(() => props.tempsGlobalS - props.course.departS);

const LABEL_ETAT = {
  pas_parti: "Pas parti",
  en_course: "En course",
  termine: "Terminé",
};

const LABEL_TYPE = { run: "course à pied", swim: "natation" };

const donnees = computed(() => {
  const { course, allure } = props.course;
  if (!allure) return null;

  const t = tempsCourseS.value;
  const kmTete = distanceAt(course, allure.premier, t);
  const kmQueue = distanceAt(course, allure.dernier, t);
  const tronconPremier = tronconActuel(course, allure.premier, t);
  const tronconDernier = tronconActuel(course, allure.dernier, t);

  let etalementM: number | null = null;
  let etalementMinutes: number | null = null;
  if (kmTete !== null && kmQueue !== null) {
    etalementM = kmTete - kmQueue;
    if (tronconDernier) {
      const allureSParM =
        tronconDernier.type === "run" ? allure.dernier.courseSParKm / 1000 : allure.dernier.nageSPar100m / 100;
      etalementMinutes = (etalementM * allureSParM) / 60;
    }
  }

  return {
    etatPremier: etatCoureur(course, allure.premier, t),
    etatDernier: etatCoureur(course, allure.dernier, t),
    kmTete,
    kmQueue,
    tronconPremier,
    tronconDernier,
    etalementM,
    etalementMinutes,
  };
});
</script>

<template>
  <section class="panneau-course" :style="{ borderLeftColor: course.couleur }">
    <h3>{{ course.nom }}</h3>

    <p v-if="!donnees" class="info-manquante">Allures non configurées — pas de simulation possible.</p>

    <template v-else>
      <dl>
        <dt>Tête</dt>
        <dd>
          {{ LABEL_ETAT[donnees.etatPremier] }}
          <span v-if="donnees.kmTete !== null">— {{ (donnees.kmTete / 1000).toFixed(2) }} km</span>
          <span v-if="donnees.tronconPremier">
            (tronçon {{ donnees.tronconPremier.numero }}, {{ LABEL_TYPE[donnees.tronconPremier.type] }})
          </span>
        </dd>

        <dt>Queue</dt>
        <dd>
          {{ LABEL_ETAT[donnees.etatDernier] }}
          <span v-if="donnees.kmQueue !== null">— {{ (donnees.kmQueue / 1000).toFixed(2) }} km</span>
          <span v-if="donnees.tronconDernier">
            (tronçon {{ donnees.tronconDernier.numero }}, {{ LABEL_TYPE[donnees.tronconDernier.type] }})
          </span>
        </dd>

        <dt>Étalement</dt>
        <dd v-if="donnees.etalementM !== null">
          {{ Math.round(donnees.etalementM) }} m
          <span v-if="donnees.etalementMinutes !== null">
            (≈ {{ formaterDureeCourte(donnees.etalementMinutes * 60) }})
          </span>
        </dd>
        <dd v-else>—</dd>
      </dl>
    </template>
  </section>
</template>

<style scoped>
.panneau-course {
  border-left: 4px solid;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.75rem;
  background: var(--couleur-surface-alt);
}

.panneau-course h3 {
  margin: 0 0 0.4rem;
  font-size: 0.95rem;
  color: var(--couleur-texte);
}

.info-manquante {
  color: var(--couleur-alerte-texte);
  font-size: 0.85rem;
  margin: 0;
}

dl {
  margin: 0;
  font-size: 0.85rem;
}

dt {
  font-weight: 600;
  margin-top: 0.3rem;
  color: var(--couleur-texte);
}

dd {
  margin: 0;
  color: var(--couleur-texte-att);
}
</style>
