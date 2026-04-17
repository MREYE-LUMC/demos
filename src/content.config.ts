import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const demos = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/demos" }),
  schema: z.object({
    title: z.string().describe("The title of the demo"),
    name: z
      .string()
      .describe(
        "Name of the demo, used on the home page and in the navigation bar.",
      ),
    description: z
      .string()
      .describe("A short description of the demo, shown on the home page."),
    weight: z.int().describe("The weight of the demo, used for sorting."),
    repoUrl: z
      .url()
      .optional()
      .describe("URL to the demo's code repository, e.g. GitHub."),
    paperUrl: z
      .url()
      .optional()
      .describe("URL to the paper associated with the demo."),
  }),
});

export const collections = { demos };
