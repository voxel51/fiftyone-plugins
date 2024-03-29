const path = require("path");
const fs = require("fs");

const PLUGINS_DIR = path.join(__dirname, "../../");
const SKELETON_DIR = path.join(__dirname, "__skeleton__");
const RENAMES = { "fiftyone.yml.template": "fiftyone.yml" };

// a function that checks if the given plugin name is a valid filename
// and does not already exist as a directory
function validatePluginName(pluginName, targetDir) {
  if (!pluginName) {
    throw new Error("No plugin name provided");
  }
  if (pluginName.includes("/")) {
    throw new Error('Plugin name cannot contain "/"');
  }
  if (pluginName.includes("\\")) {
    throw new Error('Plugin name cannot contain "\\"');
  }
  if (pluginName.includes(" ")) {
    throw new Error('Plugin name cannot contain " "');
  }
  if (fs.existsSync(targetDir)) {
    throw new Error(`Plugin "${pluginName}" already exists`);
  }
}

function main(pluginName) {
  const targetDir = path.join(PLUGINS_DIR, pluginName);
  validatePluginName(pluginName, targetDir);
  console.log(`Creating Fiftyone Plugin: "${pluginName}"`);
  console.log(`in directory ${targetDir}`);
  genPluginFiles(pluginName, SKELETON_DIR, targetDir);
}

// a function that recursively copies the given directory replacing the contents of files
// with the given replacements
function genPluginFiles(pluginName, source, destination) {
  if (!fs.existsSync(destination)) {
    fs.mkdirSync(destination);
  }
  const filepaths = fs.readdirSync(source);
  const fullPaths = filepaths.map((filepath) => path.join(source, filepath));
  const stats = fullPaths.map((filepath) => [filepath, fs.statSync(filepath)]);
  const files = stats.filter(([filepath, stat]) => stat.isFile());
  const directories = stats.filter(([filepath, stat]) => stat.isDirectory());
  for (const [directory] of directories) {
    const targetDirectory = directory.replace(source, destination);
    genPluginFiles(pluginName, directory, targetDirectory);
  }
  for (const [file] of files) {
    const targetFilepath = file.replace(source, destination);
    replaceInFile(file, targetFilepath, "{{PLUGIN_NAME}}", pluginName);
  }
}

if (require.main === module) {
  main(process.argv[2]);
}

// replace the given string in the given filepath with the given replacement string
// and return the new string
function replaceInFile(filepath, targetFilepath, string, replacement) {
  const contents = fs.readFileSync(filepath, "utf8");
  const newContents = contents.replace(new RegExp(string, "g"), replacement);
  const computedTargetFilePath = renameFile(targetFilepath);
  console.log("  CREATE", computedTargetFilePath);
  fs.writeFileSync(computedTargetFilePath, newContents, "utf8");
}

function renameFile(filePath) {
  for (const rename in RENAMES) {
    if (filePath.endsWith(rename)) {
      const pattern = new RegExp(`${rename}$`);
      return filePath.replace(pattern, RENAMES[rename]);
    }
  }
  return filePath;
}
