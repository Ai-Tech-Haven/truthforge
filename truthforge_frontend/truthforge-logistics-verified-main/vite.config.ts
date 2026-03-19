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
    },
  },
  build: {
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    rollupOptions: {
      // Safety net: if Rollup ever sees these specifiers, treat as external
      // rather than failing the build. The runtime dynamic import handles them.
      external: (id) =>
        id.includes("hedera-wallet-connect") ||
        id.includes("@hiero-ledger") ||
        id.includes("@hashgraph"),
    },
  },
});
