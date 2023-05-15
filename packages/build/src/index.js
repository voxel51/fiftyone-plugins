const defineViteConfig = require("vite").defineConfig;
const react = require("@vitejs/plugin-react").default;
const nodeResolve = require("@rollup/plugin-node-resolve").default;
const path = require("path");
const viteExternalsPlugin =
  require("vite-plugin-externals").viteExternalsPlugin;

const fiftyonePlugin = require("./rollup-plugin").default;

const isPluginBuild = process.env.STANDALONE !== "true";

// https://vitejs.dev/config/
exports.defineConfig = function defineConfig(dir) {
  const package = require(`${dir}/package.json`);
  return defineViteConfig({
    mode: "development",
    plugins: [
      fiftyonePlugin(),
      nodeResolve(),
      react(),
      isPluginBuild
        ? viteExternalsPlugin({
            react: "React",
            "react-dom": "ReactDOM",
            recoil: "recoil",
            "@fiftyone/state": "__fos__",
            "@fiftyone/operators": "__foo__",
            "@fiftyone/components": "__foc__",
            "@fiftyone/utilities": "__fou__",
            "@mui/material": "__mui__", // use mui from fiftyone
          })
        : undefined,
    ],
    build: {
      minify: true,
      lib: {
        entry: path.join(dir, package.main),
        name: package.name,
        fileName: (format) => `index.${format}.js`,
        formats: ["umd"],
      },
    },
    define: {
      "process.env.NODE_ENV": '"development"',
    },
    optimizeDeps: {
      exclude: ["react", "react-dom"],
    },
  });
};
