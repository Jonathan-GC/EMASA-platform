import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { fileURLToPath, URL } from 'node:url'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import tailwindcss from "@tailwindcss/vite";

const srcPath = resolve(fileURLToPath(new URL('./src', import.meta.url)), 'firebase-messaging-sw.js')
function firebaseSwPlugin() {
  let env = {}

  return {
    name: 'firebase-sw',
    configResolved(config) {
      env = config.env
    },
    configureServer(server) {
      server.middlewares.use('/firebase-messaging-sw.js', (req, res) => {
        res.setHeader('Content-Type', 'application/javascript')
        res.end(processSwTemplate(env))
      })
    },
    generateBundle() {
      this.emitFile({
        type: 'asset',
        fileName: 'firebase-messaging-sw.js',
        source: processSwTemplate(env)
      })
    }
  }
}

function processSwTemplate(env) {
  let template = readFileSync(srcPath, 'utf-8')
  const replacements = {
    '%%VITE_FIREBASE_API_KEY%%': JSON.stringify(env.VITE_FIREBASE_API_KEY || ''),
    '%%VITE_FIREBASE_AUTH_DOMAIN%%': JSON.stringify(env.VITE_FIREBASE_AUTH_DOMAIN || ''),
    '%%VITE_FIREBASE_PROJECT_ID%%': JSON.stringify(env.VITE_FIREBASE_PROJECT_ID || ''),
    '%%VITE_FIREBASE_MESSAGING_SENDER_ID%%': JSON.stringify(env.VITE_FIREBASE_MESSAGING_SENDER_ID || ''),
    '%%VITE_FIREBASE_APP_ID%%': JSON.stringify(env.VITE_FIREBASE_APP_ID || '')
  }
  for (const [placeholder, value] of Object.entries(replacements)) {
    template = template.replaceAll(placeholder, value)
  }
  return template
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    firebaseSwPlugin(),
    Components({
      // Auto import components from these directories (incluye subcarpetas)
      dirs: [
        'src/components/**',
        'src/layouts'
      ],

      // Auto import Ionic Vue components
      resolvers: [
        // Custom resolver for Ionic Vue components
        (componentName) => {
          if (componentName.startsWith('Ion'))
            return { name: componentName, from: '@ionic/vue' }
        }
      ],

      // Generar TypeScript definitions para auto-import (necesario incluso en proyectos JS)
      dts: true,

      // Include vue files
      include: [/\.vue$/, /\.vue\?vue/],
    })
  ],

  // Configuración de alias en el lugar correcto
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@images': fileURLToPath(new URL('./src/assets/images/', import.meta.url)),
      '@styles': fileURLToPath(new URL('./src/assets/styles/', import.meta.url)),
      '@components': fileURLToPath(new URL('./src/components/', import.meta.url)),
      '@layouts': fileURLToPath(new URL('./src/layouts/', import.meta.url)),
      '@views': fileURLToPath(new URL('./src/views/', import.meta.url)),
      '@assets': fileURLToPath(new URL('./src/assets/', import.meta.url)),
      '@utils': fileURLToPath(new URL('./src/utils/', import.meta.url)),
      '@composables': fileURLToPath(new URL('./src/composables/', import.meta.url))
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.vue',
    ],
  },
})
