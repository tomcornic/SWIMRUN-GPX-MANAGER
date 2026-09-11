import { defineStore } from "pinia";

import { type AllureCourse, type Course, longueurTotaleM, timeline } from "../simulation";
import { heureVersSecondes } from "../temps";

interface ApiTroncon {
  numero: number;
  type: "run" | "swim";
  longueur_m: number;
}

interface ApiAllureProfil {
  course_s_par_km: number;
  nage_s_par_100m: number;
}

interface ApiSimulation {
  id: number;
  nom: string;
  couleur: string;
  heure_depart: string;
  troncons: ApiTroncon[];
  allures: { premier: ApiAllureProfil; dernier: ApiAllureProfil } | null;
  trace: { type: "LineString"; coordinates: [number, number][] };
}

export interface CourseSimulation {
  id: number;
  nom: string;
  couleur: string;
  departS: number;
  course: Course;
  allure: AllureCourse | null;
  traceCoordinates: [number, number][];
}

function versProfil(p: ApiAllureProfil) {
  return { courseSParKm: p.course_s_par_km, nageSPar100m: p.nage_s_par_100m };
}

function versCourseSimulation(data: ApiSimulation): CourseSimulation {
  return {
    id: data.id,
    nom: data.nom,
    couleur: data.couleur,
    departS: heureVersSecondes(data.heure_depart),
    course: {
      troncons: data.troncons.map((t) => ({
        numero: t.numero,
        type: t.type,
        longueurM: t.longueur_m,
      })),
    },
    allure: data.allures
      ? { premier: versProfil(data.allures.premier), dernier: versProfil(data.allures.dernier) }
      : null,
    traceCoordinates: data.trace.coordinates,
  };
}

const MARGE_BORNES_S = 15 * 60;

export const useCoursesStore = defineStore("courses", {
  state: () => ({
    courses: [] as CourseSimulation[],
    chargement: false,
  }),
  getters: {
    /** [premier départ − 15 min ; dernière arrivée du dernier coureur + 15 min] (§5). */
    bornesHorloge(state): { debutS: number; finS: number } {
      const simulables = state.courses.filter((c) => c.allure !== null);
      if (simulables.length === 0) {
        return { debutS: 0, finS: 0 };
      }

      const debuts = simulables.map((c) => c.departS);
      const fins = simulables.map((c) => {
        const timingDernier = timeline(c.course, c.allure!.dernier);
        const dureeTotaleS = timingDernier.at(-1)?.sortieS ?? 0;
        return c.departS + dureeTotaleS;
      });

      return {
        debutS: Math.min(...debuts) - MARGE_BORNES_S,
        finS: Math.max(...fins) + MARGE_BORNES_S,
      };
    },
    longueurTotale(state) {
      return (courseId: number) => {
        const course = state.courses.find((c) => c.id === courseId);
        return course ? longueurTotaleM(course.course) : 0;
      };
    },
  },
  actions: {
    async charger(ids: number[]): Promise<void> {
      this.chargement = true;
      try {
        const reponses = await Promise.all(
          ids.map((id) => fetch(`/orga/courses/${id}/simulation.json`).then((r) => r.json()))
        );
        this.courses = (reponses as ApiSimulation[]).map(versCourseSimulation);
      } finally {
        this.chargement = false;
      }
    },
  },
});
