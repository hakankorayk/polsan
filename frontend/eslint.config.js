import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import { defineConfig } from "eslint/config";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

const useGeneratedClient =
  "Use the generated API client (src/api/client.ts) — docs/architecture.md, rule 6.";

export default defineConfig([
  { ignores: ["dist/", "playwright-report/", "test-results/", "src/api/schema.d.ts"] },
  js.configs.recommended,
  tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: { react, "react-hooks": reactHooks },
    languageOptions: { globals: globals.browser },
    settings: { react: { version: "detect" } },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
      // docs/security.md, Input & output
      "react/no-danger": "error",
      // docs/architecture.md, Forbidden dependencies 6
      "no-restricted-globals": ["error", { name: "fetch", message: useGeneratedClient }],
      "no-restricted-properties": [
        "error",
        { object: "window", property: "fetch", message: useGeneratedClient },
        { object: "globalThis", property: "fetch", message: useGeneratedClient },
      ],
      "no-restricted-imports": [
        "error",
        { paths: [{ name: "axios", message: useGeneratedClient }] },
      ],
    },
  },
  {
    files: ["e2e/**/*.ts", "*.config.{ts,js}", "vitest.setup.ts"],
    languageOptions: { globals: globals.node },
  },
  prettier,
]);
