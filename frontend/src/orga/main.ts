import { createPinia } from "pinia";
import { createApp } from "vue";

import "../shared/base.css";
import App from "./App.vue";
import DecoupageMapPicker from "./components/DecoupageMapPicker.vue";
import PoiMapPicker from "./components/PoiMapPicker.vue";

if (document.getElementById("app")) {
  createApp(App).use(createPinia()).mount("#app");
}

const poiMapEl = document.getElementById("poi-map-app");
if (poiMapEl) {
  const latInitial = poiMapEl.dataset.latInitial;
  const lonInitial = poiMapEl.dataset.lonInitial;
  createApp(PoiMapPicker, {
    latInputId: poiMapEl.dataset.latInput,
    lonInputId: poiMapEl.dataset.lonInput,
    latInitial: latInitial ? Number(latInitial) : undefined,
    lonInitial: lonInitial ? Number(lonInitial) : undefined,
  }).mount(poiMapEl);
}

const decoupageMapEl = document.getElementById("decoupage-map-app");
if (decoupageMapEl) {
  createApp(DecoupageMapPicker, {
    sourceUrl: decoupageMapEl.dataset.sourceUrl,
    hiddenInputId: decoupageMapEl.dataset.hiddenInput,
  }).mount(decoupageMapEl);
}
