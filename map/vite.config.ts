import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { viteExternalsPlugin } from 'vite-plugin-externals'

const isPluginBuild = process.env.STANDALONE !== 'true'

// https://vitejs.dev/config/
export default defineConfig({
  mode: 'development',
  plugins: [
    react(),
    isPluginBuild ? viteExternalsPlugin({
      react: 'React',
      'react-dom': 'ReactDOM'
    }) : undefined
  ],
  build: {
    lib: {
      entry: path.resolve(__dirname, 'src/MapPlugin.tsx'),
      name: 'MapPlugin',
      fileName: (format) => `index.${format}.js`
    }
  },
  define: {
    "process.env.NODE_ENV": '"development"',
  },
  optimizeDeps: {
    exclude: ['react', 'react-dom']
  }
})

