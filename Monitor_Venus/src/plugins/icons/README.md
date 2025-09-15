# 🎨 Sistema de Iconos Modular

Un sistema de iconos escalable y modular para el proyecto EMASA Platform Frontend.

## 📁 Estructura

```
src/plugins/icons/
├── index.js                 # Plugin principal y exportaciones
├── navigationIcons.js       # Iconos de navegación
├── actionIcons.js          # Iconos de acciones
├── statusIcons.js          # Iconos de estado e información
├── hardwareIcons.js        # Iconos de hardware y tecnología
├── locationIcons.js        # Iconos de ubicación y mapas
├── uiIcons.js              # Iconos de interfaz de usuario
├── dataIcons.js            # Iconos de datos y archivos
└── communicationIcons.js   # Iconos de comunicación y social
```

## 🚀 Instalación

### 1. Instalar el plugin (main.js)
```javascript
import { createApp } from 'vue'
import App from './App.vue'
import IconsPlugin from '@plugins/icons'

const app = createApp(App)

// Instalar con configuración por defecto
app.use(IconsPlugin)

// O con configuración personalizada
app.use(IconsPlugin, {
  prefix: '$icon',        // Prefijo para propiedades globales
  globalProperty: true,   // Habilitar propiedades globales
  provide: true          // Habilitar provide/inject
})

app.mount('#app')
```

## 📖 Uso

### 1. Usando el Composable (Recomendado)
```vue
<script setup>
import { useCommonIcons } from '@composables/useCommonIcons'

const icons = useCommonIcons()
</script>

<template>
  <ion-icon :icon="icons.chevronUp" />
  <ion-icon :icon="icons.refresh" />
  <ion-icon :icon="icons.location" />
</template>
```

### 2. Usando el Composable Avanzado
```vue
<script setup>
import { useIcons } from '@composables/useIcons'

const { getIcon, hasIcon, getIconsByCategory } = useIcons()

// Obtener icono específico
const refreshIcon = getIcon('refresh')

// Verificar si existe
const exists = hasIcon('custom-icon')

// Obtener iconos por categoría
const navIcons = getIconsByCategory('navigation')
</script>
```

### 3. Usando Propiedades Globales
```vue
<script setup>
// Acceso directo desde el componente
const refreshIcon = this.$icon('refresh')
const hasRefresh = this.$hasIcon('refresh')
</script>

<template>
  <ion-icon :icon="$icon('refresh')" />
</template>
```

### 4. Importación Directa de Módulos
```vue
<script setup>
import { navigationIcons, actionIcons } from '@plugins/icons'

// Uso directo
const chevronUp = navigationIcons['chevron-up']
const refreshIcon = actionIcons['refresh']
</script>
```

## 🎯 Categorías Disponibles

### Navigation Icons
- `chevron-up`, `chevron-down`, `chevron-back`, `chevron-forward`
- `arrow-back`, `arrow-forward`, `caret-up`, `caret-down`

### Action Icons
- `eye`, `refresh`, `add`, `edit`, `delete`
- `download`, `upload`, `copy`, `save`, `print`, `share`
- `play`, `pause`, `stop`

### Status Icons
- `alert`, `success`, `warning`, `info`, `error`, `help`
- `time`, `flash`, `shield`, `lock-closed`, `lock-open`

### Hardware Icons
- `chip`, `device`, `server`, `cloud`, `wifi`, `bluetooth`
- `desktop`, `laptop`, `tablet`, `camera`, `video`, `microphone`

### Location Icons
- `location`, `map`, `navigate`, `compass`, `globe`
- `home`, `business`, `car`, `train`, `airplane`

### UI Icons
- `search`, `filter`, `menu`, `settings`, `options`
- `list`, `grid`, `apps`, `layers`, `resize`

### Data Icons
- `document`, `folder`, `folder-open`, `archive`
- `cloud-download`, `cloud-upload`, `attach`, `link`
- `code`, `terminal`, `library`, `bookmark`

### Communication Icons
- `mail`, `chat`, `call`, `video-call`, `share`
- `heart`, `thumbs-up`, `thumbs-down`, `star`
- `person`, `people`, `notifications`

## ✨ Características

### 🔧 Modular
- Cada categoría en su propio archivo
- Importación selectiva para mejor performance
- Fácil mantenimiento y extensión

### 🚀 Performance
- Tree-shaking automático
- Solo se importan los iconos que se usan
- Sin importaciones innecesarias

### 🎨 Flexible
- Múltiples formas de uso
- Configuración personalizable
- Compatible con composables y Options API

### 📱 Responsive
- Todos los iconos son vectoriales
- Soporte completo para Ionic
- Escalables sin pérdida de calidad

## 🛠 Extensión

### Agregar nuevos iconos a una categoría existente
```javascript
// En actionIcons.js
import { newActionIcon } from 'ionicons/icons'

export const actionIcons = {
  // ... iconos existentes
  'new-action': newActionIcon
}
```

### Crear nueva categoría
```javascript
// Crear categoryIcons.js
import { icon1, icon2 } from 'ionicons/icons'

export const categoryIcons = {
  'icon-1': icon1,
  'icon-2': icon2
}

// Agregar a index.js
import { categoryIcons } from './categoryIcons.js'
// ... resto de imports

const allIcons = {
  // ... otros iconos
  ...categoryIcons
}
```

## 🎯 Mejores Prácticas

1. **Usa el composable `useCommonIcons`** para iconos frecuentes
2. **Usa `useIcons`** para funcionalidades avanzadas
3. **Importa directamente** solo cuando necesites optimización extrema
4. **Mantén consistencia** en nombres de iconos
5. **Documenta nuevos iconos** cuando los agregues

## 🔄 Migración desde el sistema anterior

```vue
<!-- Antes -->
<script setup>
import { refreshOutline, eyeOutline } from 'ionicons/icons'
</script>

<!-- Después -->
<script setup>
import { useCommonIcons } from '@composables/useCommonIcons'
const icons = useCommonIcons()
</script>

<template>
  <!-- Cambiar de refreshOutline a icons.refresh -->
  <ion-icon :icon="icons.refresh" />
  <ion-icon :icon="icons.eye" />
</template>
```
