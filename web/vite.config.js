import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Built into docs/app so GitHub Pages (main branch, /docs folder) serves it with no CI step.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { outDir: "../docs/app", emptyOutDir: true, chunkSizeWarningLimit: 900 },
});
