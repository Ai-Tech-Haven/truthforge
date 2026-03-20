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
    // No externals — @hashgraph packages are bundled normally
  },
  optimizeDeps: {
    // Pre-bundle these so Vite doesn't choke on their ESM-only dist
    include: [
      "@hashgraph/hedera-wallet-connect",
      "@hiero-ledger/sdk",
    ],
  },
});
