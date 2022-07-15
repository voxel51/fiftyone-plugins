import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { viteExternalsPlugin } from 'vite-plugin-externals'

const isPluginBuild = process.env.STANDALONE !== 'true'


// https://vitejs.dev/config/
export default defineConfig({
  mode: 'development',
  build: {
    lib: {
      entry: path.resolve(__dirname, 'src/main.ts'),
      name: 'PointCloudLookerPlugin',
      fileName: (format) => `index.${format}.js`,
      formats: ['umd']
    },
    minify: false
  },
  define: {
    "process.env.NODE_ENV": '"development"',
  },
  publicDir: isPluginBuild ? null : 'example_data'
})

