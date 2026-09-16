import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import vue from "@vitejs/plugin-vue";
import { defineConfig, type Plugin } from "vite";

/**
 * maplibre-gl-worker.mjs importe statiquement `./maplibre-gl-shared.mjs` (nom littéral, non
 * réécrit par Vite/Rollup en mode `?url`). Les deux fichiers doivent donc être copiés tels quels,
 * côte à côte, sous leur nom d'origine — voir la décision dans CLAUDE.md sur le worker maplibre-gl.
 */
function copyMaplibreWorkerFiles(): Plugin {
  const maplibreDistDir = resolve(import.meta.dirname, "node_modules/maplibre-gl/dist");
  return {
    name: "copy-maplibre-worker-files",
    apply: "build",
    buildStart() {
      for (const file of ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"]) {
        this.emitFile({
          type: "asset",
          fileName: `assets/${file}`,
          source: readFileSync(resolve(maplibreDistDir, file)),
        });
      }
    },
  };
}

export default defineConfig({
  plugins: [vue(), copyMaplibreWorkerFiles()],
  base: "/static/dist/",
  build: {
    manifest: true,
    outDir: resolve(import.meta.dirname, "../backend/app/static/dist"),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        orga: resolve(import.meta.dirname, "src/orga/main.ts"),
        public: resolve(import.meta.dirname, "src/public/main.ts"),
        theme: resolve(import.meta.dirname, "src/shared/theme.css"),
      },
    },
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
    },
  },
});
