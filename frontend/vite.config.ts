/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Set API_URL if the backend runs on another port, e.g. API_URL=http://localhost:8010
  server: { proxy: { "/api": process.env.API_URL ?? "http://localhost:8000" } },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    globals: false,
  },
});
