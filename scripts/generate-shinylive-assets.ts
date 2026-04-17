import { existsSync, rmSync, mkdirSync, readdirSync } from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const astroRoot = process.cwd();
const exportRoot = path.join(astroRoot, "public", "shinylive");
const demos = readdirSync(path.join(astroRoot, "demos"), {
  withFileTypes: true,
})
  .filter((item) => item.isDirectory())
  .map((dir) => dir.name);

if (existsSync(exportRoot)) {
  rmSync(exportRoot, { recursive: true, force: true });
}

mkdirSync(exportRoot, { recursive: true });

for (const demo of demos) {
  const sourceDir = path.join(astroRoot, "demos", demo);
  execFileSync(
    "uv",
    ["run", "shinylive", "export", sourceDir, exportRoot, "--subdir", demo],
    {
      cwd: astroRoot,
      stdio: "inherit",
    },
  );

  console.log(`Exported ${demo} to ${path.join(exportRoot, demo)}.`);
}
