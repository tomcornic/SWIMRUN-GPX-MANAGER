import { defineStore } from "pinia";

import {
  chargerCourse,
  chargerMeta,
  chargerPois,
  type CourseParcours,
  type MetaEvenement,
  type PoiParcours,
} from "../parcours";

export const useParcoursStore = defineStore("parcours", {
  state: () => ({
    meta: null as MetaEvenement | null,
    courseActiveId: null as number | null,
    courses: {} as Record<number, CourseParcours>,
    pois: {} as Record<number, PoiParcours[]>,
    distanceM: 0,
    suivreCurseur: true,
    chargement: false,
    erreur: false,
  }),
  getters: {
    courseActive(state): CourseParcours | null {
      return state.courseActiveId !== null ? (state.courses[state.courseActiveId] ?? null) : null;
    },
    poisActifs(state): PoiParcours[] {
      return state.courseActiveId !== null ? (state.pois[state.courseActiveId] ?? []) : [];
    },
  },
  actions: {
    async initialiser(): Promise<void> {
      this.chargement = true;
      try {
        const meta = await chargerMeta();
        this.meta = meta;
        if (!meta || meta.courses.length === 0) {
          this.erreur = true;
          return;
        }
        await this.selectionnerCourse(meta.courses[0].id);
      } finally {
        this.chargement = false;
      }
    },
    async selectionnerCourse(id: number): Promise<void> {
      this.courseActiveId = id;
      this.distanceM = 0;
      if (this.courses[id]) return;

      const version = this.meta?.genereLe ?? "0";
      const [course, pois] = await Promise.all([chargerCourse(id, version), chargerPois(id, version)]);
      if (course) this.courses[id] = course;
      this.pois[id] = pois;
    },
    definirDistance(distanceM: number): void {
      const total = this.courseActive?.longueurTotaleM ?? 0;
      this.distanceM = Math.min(Math.max(distanceM, 0), total);
    },
  },
});
