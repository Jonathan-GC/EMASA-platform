<template>
  <ion-item :class="['custom', itemClass]">
    <ion-label position="stacked" class="!mb-2">{{ label }}</ion-label>
    <ion-input
      :value="modelValue"
      :type="passwordInputType"
      :placeholder="placeholder"
      :disabled="disabled"
      @ionInput="onInput"
      class="custom"
      fill="solid"
    >
      <ion-button
        tabindex="-1"
        v-if="showToggle"
        fill="clear"
        slot="end"
        @click.prevent.stop="togglePasswordVisibility"
        class="password-toggle-btn rounded-full"
        :aria-label="showPassword ? 'Hide password' : 'Show password'"
      >
        <ion-icon :icon="showPassword ? icons.eyeOff : icons.eye" color="medium" slot="icon-only"></ion-icon>
      </ion-button>
    </ion-input>
  </ion-item>
</template>

<script setup>
import { ref, computed, inject } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  label: {
    type: String,
    default: 'Contraseña'
  },
  placeholder: {
    type: String,
    default: '*****'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  showToggle: {
    type: Boolean,
    default: true
  },
  itemClass: {
    type: [String, Object, Array],
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const icons = inject('icons', {})
const showPassword = ref(false)

const passwordInputType = computed(() => (showPassword.value ? 'text' : 'password'))

function togglePasswordVisibility() {
  showPassword.value = !showPassword.value
}

function onInput(e) {
  // ion-input emits ionInput events with detail.value
  const val = e?.detail?.value ?? e?.target?.value ?? ''
  emit('update:modelValue', val)
}
</script>

<style scoped>
.password-toggle-btn {
  --padding: 0;
}
</style>