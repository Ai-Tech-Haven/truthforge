import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/webhook': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      // Node polyfills required by WalletConnect / hedera-wallet-connect
      buffer: "buffer",
      process: "process/browser",
      util: "util",
      stream: "stream-browserify",
      events: "events",
    },
  },
  define: {
    // Required by WalletConnect internals
    global: "globalThis",
  },
  optimizeDeps: {
    include: ["buffer", "process"],
  },
});
