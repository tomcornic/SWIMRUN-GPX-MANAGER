import { defineStore } from "pinia";

export const VITESSES = [1, 10, 30, 60, 120] as const;
export type Vitesse = (typeof VITESSES)[number];

export const useHorlogeStore = defineStore("horloge", {
  state: () => ({
    tempsS: 0,
    borneDebutS: 0,
    borneFinS: 0,
    enLecture: false,
    vitesse: 60 as Vitesse,
  }),
  actions: {
    initialiserBornes(debutS: number, finS: number): void {
      this.borneDebutS = debutS;
      this.borneFinS = finS;
      this.tempsS = debutS;
    },
    definirTemps(t: number): void {
      this.tempsS = Math.min(Math.max(t, this.borneDebutS), this.borneFinS);
    },
    /** Avance l'horloge de deltaReelS secondes réelles écoulées, à la vitesse courante. */
    avancer(deltaReelS: number): void {
      if (!this.enLecture) return;
      const prochain = this.tempsS + deltaReelS * this.vitesse;
      this.definirTemps(prochain);
      if (prochain >= this.borneFinS) {
        this.enLecture = false;
      }
    },
    basculerLecture(): void {
      if (this.tempsS >= this.borneFinS) {
        this.tempsS = this.borneDebutS;
      }
      this.enLecture = !this.enLecture;
    },
    definirVitesse(v: Vitesse): void {
      this.vitesse = v;
    },
  },
});
