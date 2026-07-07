# 🎨 Consolidated Icon System

A unified and scalable icon system for the EMASA Platform Frontend project.

```
src/plugins/icons/
├── index.js          # Main plugin and exports
├── icons.js          # Consolidated file with all icons
└── README.md         # This documentation
```

## 🚀 Installation

### 1. Install the plugin (main.js)
```javascript
import { createApp } from 'vue'
import App from './App.vue'
import IconsPlugin from '@plugins/icons'

const app = createApp(App)

// Install with default configuration
app.use(IconsPlugin)

app.mount('#app')
```

## 📖 Usage

### 1. Using Global Properties (Recommended)
```vue
<script setup>
// Icons are available globally
</script>

<template>
  <ion-icon :icon="icons.eye" />
  <ion-icon :icon="icons.refresh" />
  <ion-icon :icon="icons.location" />
</template>
```

### 2. Using the getIcon Helper
```vue
<script setup>
// Direct access from component
const refreshIcon = getCurrentInstance().proxy.$icon('refresh')
</script>

<template>
  <ion-icon :icon="refreshIcon" />
</template>
```

### 3. Using the Name Attribute (Requires Global Registration)
```vue
<template>
  <!-- Only works if you enable global icon registration -->
  <ion-icon name="eye-outline" />
  <ion-icon name="refresh-outline" />
  <ion-icon name="people-outline" />
</template>
```

## 🎯 Available Icons

### Navigation Icons
- `chevronUp`, `chevronDown`, `chevronBack`, `chevronForward`
- `arrowBack`, `arrowForward`, `caretUp`, `caretDown`

### Action Icons
- `eye`, `refresh`, `add`, `edit`, `delete`
- `download`, `upload`, `copy`, `save`, `print`, `share`
- `play`, `pause`, `stop`, `key`, `logOut`, `shield`

### Status Icons
- `alert`, `alertCircle`, `success`, `warning`, `info`, `error`, `help`
- `time`, `power`, `shield`, `lock-closed`, `lock-open`, `flash`
- `lock-closed-outline`, `lock-open-outline`, `flash-outline`

### Hardware Icons
- `hardwareChip`, `phonePortrait`, `server`, `cloud`, `wifi`, `bluetooth`
- `desktop`, `laptop`, `tablet`, `camera`, `video`, `microphone`
- `batteryFull`, `batteryHalf`, `plug` (custom SVG)

### Location Icons
- `location`, `map`, `navigate`, `compass`, `globe`
- `home`, `business`, `car`, `train`, `airplane`, `building`

### UI Icons
- `search`, `filter`, `menu`, `settings`, `options`
- `list`, `grid`, `apps`, `layers`, `resize`

### Data Icons
- `document`, `folder`, `folder-open`, `archive`
- `cloud-download`, `cloud-upload`, `attach`, `link`
- `code`, `terminal`, `library`, `bookmark`, `analytics`

### Communication Icons
- `mail`, `chat`, `call`, `video-call`, `share`
- `heart`, `thumbs-up`, `thumbs-down`, `star`
- `person`, `people`, `notifications`

## ✨ Features

### 🔧 Consolidated
- All icons in a single `icons.js` file
- Easier maintenance and search
- Consistent naming (camelCase)

### 🚀 Performance
- Automatic tree-shaking
- Only icons that are used get included
- Optional global registration for using `name` attribute

### 🎨 Flexible
- Three ways to use: `:icon` prop, `name` attribute, or helper functions
- Compatible with composables and Options API
- Descriptive and consistent names

### 📱 Responsive
- All icons are vectorial
- Soporte completo para Ionic
- Scalable without quality loss

## 🛠 Extension

### Adding new icons
```javascript
// In icons.js
import { newIconOutline } from 'ionicons/icons'

export const icons = {
  // ... existing icons
  'newIcon': newIconOutline
}
```

## 🎯 Best Practices

1. **Use the `:icon` prop** for direct and reliable access
2. **Maintain consistency** in icon names (camelCase)
3. **Document new icons** when you add them
4. **Group related icons** in comments in `icons.js`
5. **Use the `getIcon()` helper** for programmatic access

## 🔄 Migration from Previous System

```vue
<!-- Previous system (separate files) -->
<script setup>
import { navigationIcons, actionIcons } from '@plugins/icons'
const chevronUp = navigationIcons['chevronUp']
const refreshIcon = actionIcons['refresh']
</script>

<!-- Consolidated system (single file) -->
<script setup>
// Icons are available globally
</script>

<template>
  <ion-icon :icon="icons.chevronUp" />
  <ion-icon :icon="icons.refresh" />
</template>
```

## 📋 Migration Checklist

- [x] Consolidate all icons in `icons.js`
- [x] Update `index.js` to import from consolidated file
- [x] Verify all components work with new names
- [ ] Optional: Enable global registration to use `name` attribute
- [ ] Remove old category files when everything works
