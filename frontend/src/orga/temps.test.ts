import { describe, expect, it } from "vitest";

import { formaterDureeCourte, formaterHMS, heureVersSecondes } from "./temps";

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
