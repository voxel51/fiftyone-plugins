const path = require("path");
const fs = require("fs");

const ROOT_DIR = path.join(__dirname, "..");
const PACKAGES_DIR = path.join(ROOT_DIR, "plugins");
const { FIFTYONE_DIR } = process.env;
const FIFTYONE_PACKAGES_DIR = path.join(FIFTYONE_DIR, "app/packages");
const tsConfigFO = {
  compilerOptions: {
    paths: {},
  },
};

// Add fiftyone packages paths to tsConfigFO
const excludedPackages = ["desktop"];
const packages = fs.readdirSync(FIFTYONE_PACKAGES_DIR);
for (const package of packages) {
  const packagePath = path.join(FIFTYONE_PACKAGES_DIR, package);
  const packageJSONPath = path.join(packagePath, "package.json");
  if (!fs.existsSync(packageJSONPath) || excludedPackages.includes(package))
    continue;
  const packageJSON = JSON.parse(fs.readFileSync(packageJSONPath, "utf-8"));
  tsConfigFO.compilerOptions.paths[packageJSON.name] = [packagePath];
}

// Generate tsconfig.fo.json files for plugins
const excludedPlugins = ["build", "create"];
const plugins = fs.readdirSync(PACKAGES_DIR);
for (const plugin of plugins) {
  const pluginPath = path.resolve(PACKAGES_DIR, plugin);
  const tsConfigPath = path.resolve(pluginPath, "tsconfig.json");
  const tsConfigFOPath = path.resolve(pluginPath, "tsconfig.fo.json");
  if (!fs.existsSync(tsConfigPath) || excludedPlugins.includes(plugin))
    continue;

  fs.writeFileSync(tsConfigFOPath, JSON.stringify(tsConfigFO, null, 2));
}
