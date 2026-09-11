import { describe, expect, it } from "vitest";

import {
  messagePassage,
  passageActifA,
  prochainPoi,
  tronconALaDistance,
} from "./navigation";
import type { CourseParcours, GroupePassagesParcours, PoiParcours } from "./parcours";

const COURSE: CourseParcours = {
  id: 1,
  nom: "Course XS",
  couleur: "#1d4ed8",
  troncons: [
    { numero: 1, type: "run", debutM: 0, finM: 600 },
    { numero: 2, type: "swim", debutM: 600, finM: 850 },
  ],
  passagesMultiples: [],
  trace: [],
  longueurTotaleM: 850,
};

describe("tronconALaDistance", () => {
  it("trouve le premier tronçon en début de parcours", () => {
    const position = tronconALaDistance(COURSE, 100);
    expect(position?.troncon.numero).toBe(1);
    expect(position?.index).toBe(0);
    expect(position?.total).toBe(2);
    expect(position?.distanceRestanteM).toBe(500);
  });

  it("trouve le second tronçon après la limite du premier", () => {
    const position = tronconALaDistance(COURSE, 700);
    expect(position?.troncon.numero).toBe(2);
    expect(position?.distanceRestanteM).toBe(150);
  });

  it("clampe une distance négative au début du parcours", () => {
    expect(tronconALaDistance(COURSE, -50)?.troncon.numero).toBe(1);
  });

  it("clampe une distance au-delà de la fin au dernier tronçon", () => {
    expect(tronconALaDistance(COURSE, 10_000)?.troncon.numero).toBe(2);
  });

  it("renvoie null pour un parcours sans tronçon", () => {
    expect(tronconALaDistance({ ...COURSE, troncons: [] }, 100)).toBeNull();
  });
});

describe("prochainPoi", () => {
  const pois: PoiParcours[] = [
    {
      id: 1,
      type: "ravitaillement",
      nom: "Ravito",
      description: "",
      lat: 0,
      lon: 0,
      cotePassage: null,
      distanceM: 300,
    },
    {
      id: 2,
      type: "sortie_eau",
      nom: "Sortie",
      description: "",
      lat: 0,
      lon: 0,
      cotePassage: null,
      distanceM: 700,
    },
  ];

  it("trouve le POI le plus proche en avant", () => {
    const resultat = prochainPoi(pois, 100);
    expect(resultat?.poi.nom).toBe("Ravito");
    expect(resultat?.distanceM).toBe(200);
  });

  it("passe au POI suivant une fois le premier dépassé", () => {
    const resultat = prochainPoi(pois, 400);
    expect(resultat?.poi.nom).toBe("Sortie");
  });

  it("renvoie null après le dernier POI", () => {
    expect(prochainPoi(pois, 800)).toBeNull();
  });
});

describe("passageActifA", () => {
  const groupes: GroupePassagesParcours[] = [
    { passages: [{ debutM: 100, finM: 200 }, { debutM: 400, finM: 500 }] },
  ];

  it("détecte le premier passage", () => {
    const actif = passageActifA(groupes, 150);
    expect(actif).toEqual({ groupeIndex: 0, numeroPassage: 1, totalPassages: 2 });
  });

  it("détecte le second passage", () => {
    const actif = passageActifA(groupes, 450);
    expect(actif).toEqual({ groupeIndex: 0, numeroPassage: 2, totalPassages: 2 });
  });

  it("renvoie null en dehors de toute portion multiple", () => {
    expect(passageActifA(groupes, 300)).toBeNull();
  });
});

describe("messagePassage", () => {
  it("formate le premier passage", () => {
    expect(messagePassage({ groupeIndex: 0, numeroPassage: 1, totalPassages: 2 })).toBe(
      "1er passage — portion empruntée 2 fois."
    );
  });

  it("formate un passage ultérieur", () => {
    expect(messagePassage({ groupeIndex: 0, numeroPassage: 2, totalPassages: 2 })).toBe(
      "2e passage — portion empruntée 2 fois."
    );
  });
});
