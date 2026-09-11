import { describe, expect, it } from "vitest";

import {
  type AllureCourse,
  type Course,
  distanceAt,
  etatCoureur,
  longueurTotaleM,
  plageAt,
  timeline,
  tronconActuel,
  validerAllure,
} from "./simulation";

// Cas de référence du cahier des charges (§5) :
// tronçon 1 Run 1000 m à 5:00/km, tronçon 2 Swim 200 m à 2:00/100 m.
const courseReference: Course = {
  troncons: [
    { numero: 1, type: "run", longueurM: 1000 },
    { numero: 2, type: "swim", longueurM: 200 },
  ],
};

const profilReference = { courseSParKm: 300, nageSPar100m: 120 }; // 5:00/km, 2:00/100m

describe("timeline", () => {
  it("calcule les heures et distances d'entrée/sortie de chaque tronçon", () => {
    const result = timeline(courseReference, profilReference);

    expect(result).toEqual([
      { numero: 1, type: "run", entreeS: 0, sortieS: 300, entreeDistanceM: 0, sortieDistanceM: 1000 },
      {
        numero: 2,
        type: "swim",
        entreeS: 300,
        sortieS: 540,
        entreeDistanceM: 1000,
        sortieDistanceM: 1200,
      },
    ]);
  });

  it("renvoie un tableau vide pour une course sans tronçon", () => {
    expect(timeline({ troncons: [] }, profilReference)).toEqual([]);
  });
});

describe("distanceAt", () => {
  it("cas de référence : 1050 m à t = départ + 6 min", () => {
    expect(distanceAt(courseReference, profilReference, 6 * 60)).toBeCloseTo(1050, 6);
  });

  it("aucune position avant le départ", () => {
    expect(distanceAt(courseReference, profilReference, -1)).toBeNull();
  });

  it("position exacte au départ", () => {
    expect(distanceAt(courseReference, profilReference, 0)).toBe(0);
  });

  it("bloqué à la distance totale après l'arrivée", () => {
    expect(distanceAt(courseReference, profilReference, 10_000)).toBe(1200);
  });

  it("position exacte à la jonction entre deux tronçons", () => {
    expect(distanceAt(courseReference, profilReference, 300)).toBe(1000);
  });
});

describe("plageAt", () => {
  const allure: AllureCourse = {
    premier: { courseSParKm: 300, nageSPar100m: 120 },
    dernier: { courseSParKm: 420, nageSPar100m: 180 },
  };

  it("le premier est toujours devant ou égal au dernier", () => {
    const plage = plageAt(courseReference, allure, 200);
    expect(plage.finM).not.toBeNull();
    expect(plage.debutM).not.toBeNull();
    expect(plage.finM as number).toBeGreaterThanOrEqual(plage.debutM as number);
  });

  it("plage nulle avant le départ", () => {
    const plage = plageAt(courseReference, allure, -10);
    expect(plage).toEqual({ debutM: null, finM: null });
  });

  it("les deux coureurs convergent à l'arrivée", () => {
    const plage = plageAt(courseReference, allure, 10_000);
    expect(plage.debutM).toBe(1200);
    expect(plage.finM).toBe(1200);
  });
});

describe("etatCoureur", () => {
  it("pas encore parti avant le départ", () => {
    expect(etatCoureur(courseReference, profilReference, -5)).toBe("pas_parti");
  });

  it("en course entre le départ et l'arrivée", () => {
    expect(etatCoureur(courseReference, profilReference, 100)).toBe("en_course");
  });

  it("terminé après la sortie du dernier tronçon", () => {
    expect(etatCoureur(courseReference, profilReference, 540)).toBe("termine");
  });
});

describe("tronconActuel", () => {
  it("renvoie null avant le départ", () => {
    expect(tronconActuel(courseReference, profilReference, -5)).toBeNull();
  });

  it("trouve le premier tronçon en début de course", () => {
    expect(tronconActuel(courseReference, profilReference, 10)?.numero).toBe(1);
  });

  it("trouve le second tronçon une fois le premier terminé", () => {
    expect(tronconActuel(courseReference, profilReference, 400)?.numero).toBe(2);
  });

  it("reste sur le dernier tronçon après l'arrivée", () => {
    expect(tronconActuel(courseReference, profilReference, 10_000)?.numero).toBe(2);
  });
});

describe("longueurTotaleM", () => {
  it("additionne la longueur de tous les tronçons", () => {
    expect(longueurTotaleM(courseReference)).toBe(1200);
  });
});

describe("validerAllure", () => {
  it("accepte un premier plus rapide que le dernier sur les deux disciplines", () => {
    expect(
      validerAllure({
        premier: { courseSParKm: 300, nageSPar100m: 120 },
        dernier: { courseSParKm: 420, nageSPar100m: 180 },
      })
    ).toEqual([]);
  });

  it("rejette un premier plus lent en course à pied", () => {
    const erreurs = validerAllure({
      premier: { courseSParKm: 420, nageSPar100m: 120 },
      dernier: { courseSParKm: 300, nageSPar100m: 180 },
    });
    expect(erreurs).toHaveLength(1);
    expect(erreurs[0]).toMatch(/course à pied/);
  });

  it("rejette un premier plus lent en natation", () => {
    const erreurs = validerAllure({
      premier: { courseSParKm: 300, nageSPar100m: 180 },
      dernier: { courseSParKm: 420, nageSPar100m: 120 },
    });
    expect(erreurs).toHaveLength(1);
    expect(erreurs[0]).toMatch(/natation/);
  });
});
