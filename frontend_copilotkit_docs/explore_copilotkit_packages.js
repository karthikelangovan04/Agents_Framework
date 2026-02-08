#!/usr/bin/env node
/**
 * Explore CopilotKit and @ag-ui packages in the reference frontend (read-only).
 * Run from repo root: node frontend_copilotkit_docs/explore_copilotkit_packages.js
 * Requires: Adk_Copilotkit_UI_App/frontend/package.json and node_modules.
 */
const path = require("path");
const fs = require("fs");

const REPO_ROOT = path.resolve(__dirname, "..");
const FRONTEND_DIR = path.join(REPO_ROOT, "Adk_Copilotkit_UI_App", "frontend");
const PACKAGE_JSON = path.join(FRONTEND_DIR, "package.json");
const NODE_MODULES = path.join(FRONTEND_DIR, "node_modules");

const SCOPE_NAMES = ["@copilotkit", "@ag-ui"];

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (e) {
    return null;
  }
}

function main() {
  console.log("Frontend CopilotKit package exploration");
  console.log("Repo root:", REPO_ROOT);
  console.log("Frontend (reference, read-only):", FRONTEND_DIR);
  console.log("");

  const appPkg = readJson(PACKAGE_JSON);
  if (!appPkg) {
    console.error("Missing or invalid:", PACKAGE_JSON);
    process.exit(1);
  }

  const result = {
    source: {
      packageJson: PACKAGE_JSON,
      frontendDir: FRONTEND_DIR,
    },
    app: {
      name: appPkg.name,
      version: appPkg.version,
      dependencies: appPkg.dependencies || {},
      devDependencies: appPkg.devDependencies || {},
    },
    packages: {},
  };

  const deps = { ...(appPkg.dependencies || {}), ...(appPkg.devDependencies || {}) };

  for (const scope of SCOPE_NAMES) {
    const scopePath = path.join(NODE_MODULES, scope);
    if (!fs.existsSync(scopePath) || !fs.statSync(scopePath).isDirectory()) continue;

    const subdirs = fs.readdirSync(scopePath);
    for (const name of subdirs) {
      const pkgName = `${scope}/${name}`;
      const pkgDir = path.join(scopePath, name);
      const pkgJsonPath = path.join(pkgDir, "package.json");
      const pkgJson = readJson(pkgJsonPath);
      if (!pkgJson) continue;

      result.packages[pkgName] = {
        version: pkgJson.version,
        main: pkgJson.main,
        module: pkgJson.module,
        types: pkgJson.types,
        exports: pkgJson.exports ? Object.keys(pkgJson.exports) : [],
        inAppDependencies: deps[pkgName] || "(transitive)",
      };
    }
  }

  console.log(JSON.stringify(result, null, 2));
}

main();
