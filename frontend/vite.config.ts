import { resolve } from "node:path";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  base: "/static/dist/",
  build: {
    manifest: true,
    outDir: resolve(import.meta.dirname, "../backend/app/static/dist"),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        orga: resolve(import.meta.dirname, "src/orga/main.ts"),
        public: resolve(import.meta.dirname, "src/public/main.ts"),
      },
    },
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
    },
  },
});
