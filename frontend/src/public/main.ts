import { createPinia } from "pinia";
import { createApp } from "vue";

import "../shared/base.css";
import "./marqueurs.css";
import App from "./App.vue";

createApp(App).use(createPinia()).mount("#app");
