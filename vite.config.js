import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'serve-data-dir',
      // Dev: serve files from data/ at /data/
      configureServer(server) {
        server.middlewares.use('/data', (req, res, next) => {
          const filePath = path.join(process.cwd(), 'data', req.url.replace(/^\//, ''))
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
        const srcDir = path.join(process.cwd(), 'data')
        const outDir = path.join(process.cwd(), 'dist', 'data')
        fs.mkdirSync(outDir, { recursive: true })
        for (const file of fs.readdirSync(srcDir)) {
          const src = path.join(srcDir, file)
          if (fs.statSync(src).isFile()) {
            fs.copyFileSync(src, path.join(outDir, file))
            console.log(`[serve-data-dir] copied ${file} -> dist/data/`)
          }
        }
      }
    }
  ],
})
