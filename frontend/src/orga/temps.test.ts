import { describe, expect, it } from "vitest";

import {
  formaterDureeCourte,
  formaterHMS,
  graduationsS,
  heureVersSecondes,
  pasGraduationS,
} from "./temps";

describe("heureVersSecondes", () => {
  it("parse HH:MM:SS", () => {
    expect(heureVersSecondes("09:30:15")).toBe(9 * 3600 + 30 * 60 + 15);
  });

  it("parse HH:MM (secondes implicites à 0)", () => {
    expect(heureVersSecondes("09:30")).toBe(9 * 3600 + 30 * 60);
  });
});

describe("formaterHMS", () => {
  it("formate avec zéros de tête", () => {
    expect(formaterHMS(9 * 3600 + 5 * 60 + 3)).toBe("09:05:03");
  });

  it("gère les valeurs négatives (avant minuit)", () => {
    expect(formaterHMS(-90)).toBe("-00:01:30");
  });

  it("arrondit à la seconde", () => {
    expect(formaterHMS(65.6)).toBe("00:01:06");
  });
});

describe("formaterDureeCourte", () => {
  it("affiche juste les minutes en dessous d'une heure", () => {
    expect(formaterDureeCourte(15 * 60)).toBe("15 min");
  });

  it("affiche heures et minutes au-delà d'une heure", () => {
    expect(formaterDureeCourte(80 * 60)).toBe("1 h 20 min");
  });
});

describe("pasGraduationS", () => {
  it("choisit le plus petit pas rond qui tient dans le nombre de graduations", () => {
    expect(pasGraduationS(40 * 60)).toBe(5 * 60); // 40 min -> toutes les 5 min
    expect(pasGraduationS(90 * 60)).toBe(10 * 60); // 1 h 30 -> toutes les 10 min
    expect(pasGraduationS(4 * 3600)).toBe(30 * 60); // 4 h -> toutes les 30 min
    expect(pasGraduationS(9 * 3600)).toBe(3600); // 9 h -> toutes les heures
  });

  it("se rabat sur le plus grand pas pour une plage très longue ou nulle", () => {
    expect(pasGraduationS(10 * 24 * 3600)).toBe(6 * 3600);
    expect(pasGraduationS(0)).toBe(5 * 60);
  });
});

describe("graduationsS", () => {
  it("donne des heures rondes à l'intérieur de la plage, pas ses bornes brutes", () => {
    // 08:45:00 -> 10:08:20 : toutes les 10 min, de 08:50 à 10:00.
    const graduations = graduationsS(8 * 3600 + 45 * 60, 10 * 3600 + 8 * 60 + 20);
    expect(graduations.map((t) => formaterHMS(t).slice(0, 5))).toEqual([
      "08:50", "09:00", "09:10", "09:20", "09:30", "09:40", "09:50", "10:00",
    ]);
  });

  it("inclut les bornes quand elles tombent rond", () => {
    expect(graduationsS(9 * 3600, 10 * 3600)).toEqual([
      32400, 33000, 33600, 34200, 34800, 35400, 36000,
    ]);
  });
});
