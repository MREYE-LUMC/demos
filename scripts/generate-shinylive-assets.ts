import {
  copyFileSync,
  existsSync,
  readFileSync,
  rmSync,
  mkdirSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { execFileSync } from "node:child_process";

const astroRoot = process.cwd();
const exportRoot = path.join(astroRoot, "public", "shinylive");
const pyodideRoot = path.join(exportRoot, "shinylive", "pyodide");
const pyodideLockfilePath = path.join(pyodideRoot, "pyodide-lock.json");
const pyodideOverridesPath = path.join(
  astroRoot,
  "scripts",
  "shinylive-pyodide-overrides.json",
);

type PyodideOverride = {
  package: string;
  sourceWheel: string;
  version: string;
};

type PyodideLockfile = {
  packages: Record<
    string,
    {
      file_name?: string;
      version?: string;
      sha256?: string;
      [key: string]: unknown;
    }
  >;
  [key: string]: unknown;
};

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

patchPyodideOverrides();

function patchPyodideOverrides() {
  if (!existsSync(pyodideLockfilePath)) {
    return;
  }

  const pyodideOverrides = JSON.parse(
    readFileSync(pyodideOverridesPath, "utf8"),
  ) as PyodideOverride[];
  const lockfile = JSON.parse(
    readFileSync(pyodideLockfilePath, "utf8"),
  ) as PyodideLockfile;

  for (const override of pyodideOverrides) {
    patchPyodidePackage(lockfile, override);
  }

  writeFileSync(pyodideLockfilePath, JSON.stringify(lockfile));
}

function patchPyodidePackage(
  lockfile: PyodideLockfile,
  override: PyodideOverride,
) {
  const packageEntry = lockfile.packages[override.package];

  if (!packageEntry) {
    throw new Error(
      `Package ${override.package} was not found in ${pyodideLockfilePath}`,
    );
  }

  const sourceWheelPath = path.join(astroRoot, override.sourceWheel);

  if (!existsSync(sourceWheelPath)) {
    throw new Error(`Source wheel not found: ${sourceWheelPath}`);
  }

  const actualSha256 = createHash("sha256")
    .update(readFileSync(sourceWheelPath))
    .digest("hex");
  const overrideSha256 = actualSha256;

  const wheelFileName = path.basename(sourceWheelPath);
  const destinationWheelPath = path.join(pyodideRoot, wheelFileName);

  copyFileSync(sourceWheelPath, destinationWheelPath);

  if (packageEntry.file_name && packageEntry.file_name !== wheelFileName) {
    const staleWheelPath = path.join(pyodideRoot, packageEntry.file_name);

    if (existsSync(staleWheelPath)) {
      rmSync(staleWheelPath);
    }
  }

  packageEntry.file_name = wheelFileName;
  packageEntry.version = override.version;
  packageEntry.sha256 = overrideSha256;

  console.log(`Patched ${override.package} -> ${override.version}`);
}
