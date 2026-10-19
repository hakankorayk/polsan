import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The SPA and the API share one origin (docs/security.md): the dev server and `vite preview`
// proxy /api to Django. API_TARGET points at the backend (e2e uses its own port).
const proxy = {
  "/api": { target: process.env.API_TARGET ?? "http://127.0.0.1:8000" },
};

export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
});
