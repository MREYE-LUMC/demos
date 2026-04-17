import { existsSync, rmSync, mkdirSync, copyFileSync } from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const astroRoot = process.cwd();
const repoRoot = path.resolve(astroRoot);
const demos = ["paros", "visisipy", "synteyes"];
const exportRoot = path.join(astroRoot, "public", "shinylive");

if (existsSync(exportRoot)) {
  rmSync(exportRoot, { recursive: true, force: true });
}

mkdirSync(exportRoot, { recursive: true });

// const iconSource = path.join(repoRoot, "_assets", "icon.png");
// const iconDestination = path.join(astroRoot, "public", "_assets", "icon.png");
// mkdirSync(path.dirname(iconDestination), { recursive: true });
// copyFileSync(iconSource, iconDestination);

// const wheelsSource = path.join(repoRoot, "_assets", "wheels");
// const wheelsDestination = path.join(astroRoot, "public", "_assets", "wheels");
// if (existsSync(wheelsDestination)) {
//   rmSync(wheelsDestination, { recursive: true, force: true });
// }
// mkdirSync(wheelsDestination, { recursive: true });
// copyFileSync(path.join(wheelsSource, "numba-0.61.2-py3-none-any.whl"), path.join(wheelsDestination, "numba-0.61.2-py3-none-any.whl"));
// copyFileSync(path.join(wheelsSource, "vtk-9.4.2-py3-none-any.whl"), path.join(wheelsDestination, "vtk-9.4.2-py3-none-any.whl"));

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
