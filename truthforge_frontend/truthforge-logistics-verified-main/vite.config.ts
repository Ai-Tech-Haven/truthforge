import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  server: {
    host: "::",
    port: 8080,
    hmr: { overlay: false },
    proxy: {
      '/api': { target: 'http://localhost:5000', changeOrigin: true },
      '/webhook': { target: 'http://localhost:5000', changeOrigin: true },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      buffer: "buffer",
      process: "process/browser",
      util: "util",
      stream: "stream-browserify",
      events: "events",
    },
  },
  define: {
    global: "globalThis",
  },
  optimizeDeps: {
    // Only pre-bundle Node polyfills — wallet-connect is loaded dynamically
    include: ["buffer", "process"],
  },
  build: {
    commonjsOptions: {
      transformMixedEsModules: true,
    },
  },
});
