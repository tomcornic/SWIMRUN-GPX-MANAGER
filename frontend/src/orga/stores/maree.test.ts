import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";

import { useMareeStore } from "./maree";

function creerStoreAvecSerie() {
  setActivePinia(createPinia());
  const store = useMareeStore();
  store.serie = [
    { secondes: 0, hauteurM: 1.0 },
    { secondes: 600, hauteurM: 2.0 },
    { secondes: 1200, hauteurM: 5.0 },
  ];
  return store;
}

describe("useMareeStore.hauteurAt", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renvoie null sans série chargée", () => {
    const store = useMareeStore();
    expect(store.hauteurAt(100)).toBeNull();
  });

  it("interpole linéairement entre deux échantillons", () => {
    const store = creerStoreAvecSerie();
    expect(store.hauteurAt(300)).toBeCloseTo(1.5);
  });

  it("renvoie la valeur exacte à un échantillon", () => {
    const store = creerStoreAvecSerie();
    expect(store.hauteurAt(600)).toBe(2.0);
  });

  it("se cale sur la première valeur avant le début de la série", () => {
    const store = creerStoreAvecSerie();
    expect(store.hauteurAt(-100)).toBe(1.0);
  });

  it("se cale sur la dernière valeur après la fin de la série", () => {
    const store = creerStoreAvecSerie();
    expect(store.hauteurAt(10_000)).toBe(5.0);
  });
});

describe("useMareeStore.tendanceAt", () => {
  it("détecte une tendance montante", () => {
    const store = creerStoreAvecSerie();
    expect(store.tendanceAt(300)).toBe("montante");
  });

  it("détecte une tendance descendante", () => {
    const store = creerStoreAvecSerie();
    store.serie = [
      { secondes: 0, hauteurM: 5.0 },
      { secondes: 600, hauteurM: 1.0 },
    ];
    expect(store.tendanceAt(300)).toBe("descendante");
  });

  it("renvoie null sans série chargée", () => {
    setActivePinia(createPinia());
    const store = useMareeStore();
    expect(store.tendanceAt(100)).toBeNull();
  });
});
