// Generates src/features/aakaash/api-types.ts from the FastAPI OpenAPI schema.
// Run from aakaash/web:  npm run gen:types
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const web = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const aakaash = resolve(web, "..");
const py = join(aakaash, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
if (!existsSync(py)) throw new Error(`Python venv not found at ${py}`);
const spec = join(web, "openapi.json");
execFileSync(py, ["-I", join(aakaash, "scripts", "dump_openapi.py"), spec], { stdio: "inherit", cwd: aakaash });
execFileSync(process.execPath, [join(web, "node_modules", "openapi-typescript", "bin", "cli.js"), spec,
  "-o", join(web, "src", "features", "aakaash", "api-types.ts")], { stdio: "inherit" });
