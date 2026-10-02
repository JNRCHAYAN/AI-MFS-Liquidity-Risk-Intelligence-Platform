import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

// eslint-config-next 16 ships ESLint flat config presets. The core-web-vitals
// entry already includes the Next.js base, React, a11y and TypeScript blocks.
const nextCoreWebVitals = require("eslint-config-next/core-web-vitals");

const config = [
  {
    ignores: [
      ".next/**",
      "out/**",
      "build/**",
      "node_modules/**",
      "next-env.d.ts",
    ],
  },
  ...nextCoreWebVitals,
];

export default config;
