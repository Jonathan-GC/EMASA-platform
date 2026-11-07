<template>
  <div class="appearance-card">
    <h3 class="appearance-title">
      <ion-icon :icon="icons.contrast"></ion-icon>
      Apariencia
    </h3>

    <div class="appearance-options" role="radiogroup" aria-label="Tema de la aplicación">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        class="appearance-option"
        :class="{ active: preference === option.value }"
        role="radio"
        :aria-checked="preference === option.value ? 'true' : 'false'"
        @click="setPreference(option.value)"
      >
        <ion-icon :icon="option.icon"></ion-icon>
        <span class="appearance-option-label">{{ option.label }}</span>
        <ion-icon
          v-if="preference === option.value"
          class="appearance-check"
          :icon="icons.checkmark"
        ></ion-icon>
      </button>
    </div>

    <p class="appearance-hint">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { useTheme } from '@/composables/useTheme'

const icons = inject('icons', {})
const { preference, resolved, setPreference } = useTheme()

const options = [
  { value: 'light', label: 'Claro', icon: icons.sunny },
  { value: 'dark', label: 'Oscuro', icon: icons.moon },
  { value: 'system', label: 'Sistema', icon: icons.contrast },
]

// Texto de ayuda: aclara qué hace "Sistema" y que se guarda localmente
const hint = computed(() => {
  if (preference.value !== 'system') return 'Se guarda en este dispositivo.'

  return resolved.value === 'dark'
    ? 'Siguiendo el sistema: oscuro.'
    : 'Siguiendo el sistema: claro.'
})
</script>

<style scoped>
.appearance-card {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: var(--app-shadow-sm);
}

.appearance-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--app-text-secondary);
}

.appearance-title ion-icon {
  font-size: 18px;
  color: var(--app-text-muted);
}

.appearance-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.appearance-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: transparent;
  color: var(--app-text-secondary);
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.appearance-option ion-icon {
  font-size: 18px;
  color: var(--app-text-muted);
}

.appearance-option:hover {
  background: var(--app-hover);
}

.appearance-option.active {
  border-color: var(--ion-color-primary);
  background: var(--app-surface-2);
  color: var(--app-text);
}

.appearance-option.active ion-icon {
  color: var(--ion-color-primary);
}

.appearance-option-label {
  flex: 1;
}

.appearance-check {
  font-size: 18px;
}

.appearance-option.active .appearance-check {
  color: var(--ion-color-primary);
}

.appearance-hint {
  margin: 10px 0 0 0;
  font-size: 0.75rem;
  color: var(--app-text-subtle);
}

@media (max-width: 768px) {
  .appearance-card {
    padding: 12px 16px;
  }
}
</style>
