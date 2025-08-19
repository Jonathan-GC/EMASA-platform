import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    Components({
      // Auto import components from these directories
      dirs: [
        'src/components',
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

      // No TypeScript definitions for JavaScript project
      dts: false,

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
