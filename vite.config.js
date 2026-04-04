import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const projectRoot = fileURLToPath(new URL('.', import.meta.url))
const dataDir = path.join(projectRoot, 'data')
const distDataDir = path.join(projectRoot, 'dist', 'data')

// https://vite.dev/config/
export default defineConfig({
  server: {
    proxy: {
      '/ask': 'http://localhost:8000',
    },
  },
  plugins: [
    react(),
    {
      name: 'serve-data-dir',
      // Dev: serve files from data/ at /data/
      configureServer(server) {
        server.middlewares.use('/data', (req, res, next) => {
          const filePath = path.join(dataDir, req.url.replace(/^\//, ''))
          if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
            const ext = path.extname(filePath)
            if (ext === '.json') res.setHeader('Content-Type', 'application/json')
            if (ext === '.geojson') res.setHeader('Content-Type', 'application/geo+json')
            fs.createReadStream(filePath).pipe(res)
          } else {
            next()
          }
        })
      },
      // Production: copy data/ into dist/data/
      closeBundle() {
        fs.mkdirSync(distDataDir, { recursive: true })
        for (const file of fs.readdirSync(dataDir)) {
          if (file.startsWith('.')) continue
          const src = path.join(dataDir, file)
          if (fs.statSync(src).isFile()) {
            fs.copyFileSync(src, path.join(distDataDir, file))
            console.log(`[serve-data-dir] copied data/${file} -> dist/data/`)
          }
        }
      }
    }
  ],
})
