# Ionic Plugin Setup

This plugin structure mirrors Vuetify's organization for better maintainability.

## Structure

```
plugins/ionic/
├── index.js       - Main plugin entry point
├── config.js      - Ionic configuration & component defaults
├── theme.js       - Theme colors & CSS variables
└── README.md      - This file

plugins/icons/
└── icons.js       - Icon configuration (outline & filled)
```

## Usage

### 1. Basic Setup (in main.js)

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import { createIonic } from '@/plugins/ionic'

const app = createApp(App)

// Use Ionic plugin
app.use(createIonic())

app.mount('#app')
```

### 2. Custom Configuration

```javascript
import { createIonic } from '@/plugins/ionic'

app.use(createIonic({
  config: {
    mode: 'ios',          // Force iOS mode
    rippleEffect: false,  // Disable ripple
  }
}))
```

### 3. Using Icons in Components

```vue
<template>
  <!-- Outline icons -->
  <ion-icon :icon="icons['eye-outline']"></ion-icon>
  <ion-icon :icon="icons['refresh-outline']"></ion-icon>
  
  <!-- Filled icons -->
  <ion-icon :icon="filledIcons['eye']"></ion-icon>
  <ion-icon :icon="filledIcons['heart']"></ion-icon>
</template>

<script setup>
import { inject } from 'vue'

// Inject icons
const icons = inject('icons', {})
const filledIcons = inject('filledIcons', {})
</script>
```

### 4. Using Theme Variables in CSS

```vue
<style scoped>
.my-component {
  /* Use theme colors */
  background-color: var(--color-amber-500);
  color: var(--color-zinc-800);
  
  /* Use spacing */
  padding: var(--spacing-md);
  margin: var(--spacing-lg);
  
  /* Use border radius */
  border-radius: var(--radius-lg);
  
  /* Use shadows */
  box-shadow: var(--shadow-md);
}
</style>
```

### 5. Available Theme Colors

**Primary/Amber:**
- `--color-amber-50` to `--color-amber-900`

**Secondary/Zinc:**
- `--color-zinc-50` to `--color-zinc-900`

**Status Colors:**
- `--color-success`, `--color-success-light`, `--color-success-dark`
- `--color-warning`, `--color-warning-light`, `--color-warning-dark`
- `--color-danger`, `--color-danger-light`, `--color-danger-dark`
- `--color-info`, `--color-info-light`, `--color-info-dark`

**Spacing:**
- `--spacing-xs` (4px)
- `--spacing-sm` (8px)
- `--spacing-md` (16px)
- `--spacing-lg` (24px)
- `--spacing-xl` (32px)
- `--spacing-2xl` (40px)
- `--spacing-3xl` (48px)

**Border Radius:**
- `--radius-sm` (4px)
- `--radius-md` (8px)
- `--radius-lg` (12px)
- `--radius-xl` (16px)
- `--radius-2xl` (24px)
- `--radius-full` (9999px)

## Configuration Options

### Ionic Config (config.js)

```javascript
{
  mode: 'md',              // 'ios' | 'md' | undefined
  animated: true,          // Enable animations
  rippleEffect: true,      // Enable ripple effect
  hardwareBackButton: true // Enable hardware back button
}
```

### Component Defaults (config.js)

Override default props for Ionic components:

```javascript
componentDefaults: {
  IonButton: {
    fill: 'solid',
    shape: 'round',
  },
  IonInput: {
    fill: 'solid',
    labelPlacement: 'floating',
  }
}
```

## Benefits

✅ **Centralized Configuration** - All Ionic settings in one place
✅ **Theme Variables** - CSS variables auto-generated and applied
✅ **Icon Management** - Both outline and filled icons organized
✅ **Type Safety Ready** - Easy to convert to TypeScript
✅ **Scalable** - Similar to Vuetify's plugin system
