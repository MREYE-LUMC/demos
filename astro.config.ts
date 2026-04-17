import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import tailwindcss from "@tailwindcss/vite";

import icon from "astro-icon";

export default defineConfig({
  site: "https://demo.mreye.nl",
  output: "static",
  integrations: [mdx(), icon()],
  vite: {
    plugins: [tailwindcss()],
  },
});
