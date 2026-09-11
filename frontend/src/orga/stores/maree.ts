import { defineStore } from "pinia";

export interface PointSerieMaree {
  secondes: number;
  hauteurM: number;
}

export interface ExtremeMaree extends PointSerieMaree {
  type: "pm" | "bm";
}

interface ApiPointSerie {
  secondes: number;
  hauteur_m: number;
}

interface ApiExtreme extends ApiPointSerie {
  type: "pm" | "bm";
}

interface ApiSerieMaree {
  serie: ApiPointSerie[];
  extremes: ApiExtreme[];
}

export const useMareeStore = defineStore("maree", {
  state: () => ({
    serie: [] as PointSerieMaree[],
    extremes: [] as ExtremeMaree[],
    chargement: false,
  }),
  getters: {
    /** Hauteur interpolée linéairement entre échantillons (déjà espacés de 5 min côté API). */
    hauteurAt() {
      return (secondes: number): number | null => {
        const points = this.serie;
        if (points.length === 0) return null;
        if (secondes <= points[0].secondes) return points[0].hauteurM;
        const dernier = points[points.length - 1];
        if (secondes >= dernier.secondes) return dernier.hauteurM;

        for (let i = 0; i < points.length - 1; i++) {
          const a = points[i];
          const b = points[i + 1];
          if (secondes >= a.secondes && secondes <= b.secondes) {
            const ratio = b.secondes === a.secondes ? 0 : (secondes - a.secondes) / (b.secondes - a.secondes);
            return a.hauteurM + ratio * (b.hauteurM - a.hauteurM);
          }
        }
        return null;
      };
    },
    tendanceAt() {
      return (secondes: number): "montante" | "descendante" | null => {
        const h1 = this.hauteurAt(secondes - 60);
        const h2 = this.hauteurAt(secondes + 60);
        if (h1 === null || h2 === null || h1 === h2) return null;
        return h2 > h1 ? "montante" : "descendante";
      };
    },
  },
  actions: {
    async charger(debutS: number, finS: number): Promise<void> {
      this.chargement = true;
      try {
        const params = new URLSearchParams({
          debut_s: String(Math.round(debutS)),
          fin_s: String(Math.round(finS)),
        });
        const reponse = await fetch(`/orga/maree/serie.json?${params}`);
        const data = (await reponse.json()) as ApiSerieMaree;
        this.serie = data.serie.map((p) => ({ secondes: p.secondes, hauteurM: p.hauteur_m }));
        this.extremes = data.extremes.map((e) => ({
          secondes: e.secondes,
          hauteurM: e.hauteur_m,
          type: e.type,
        }));
      } finally {
        this.chargement = false;
      }
    },
  },
});
