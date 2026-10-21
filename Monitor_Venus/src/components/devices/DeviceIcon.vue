<template>
  <div class="device-icon" :class="{ 'with-circle': circle }" :style="wrapStyle">
    <ion-icon :icon="mainIcon" :style="mainStyle"></ion-icon>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { resolveDeviceInfo, getDeviceIconKey } from '@/utils/auth/deviceIcons.js'
import { getCurrentDeviceInfo } from '@/utils/auth/deviceTrust.js'

const props = defineProps({
  // User-Agent crudo de la sesión (p. ej. session.user_agent)
  userAgent: { type: String, default: '' },
  // Nombre legible del dispositivo (respaldo si el UA no dice nada)
  deviceName: { type: String, default: '' },
  // Detectar el dispositivo actual vía navigator/Capacitor en vez de un UA dado
  current: { type: Boolean, default: false },
  // Tamaño del icono en px
  size: { type: Number, default: 20 },
  // Círculo gris de fondo (como en la lista de sesiones)
  circle: { type: Boolean, default: true },
  // Color del icono (valor CSS de color)
  color: { type: String, default: 'var(--ion-color-medium)' }
})

const icons = inject('icons', {})

const iconKey = computed(() => {
  const info = props.current
    ? getCurrentDeviceInfo()
    : resolveDeviceInfo({ userAgent: props.userAgent, deviceName: props.deviceName })

  return getDeviceIconKey(info)
})

const mainIcon = computed(() => icons[iconKey.value] || icons.globe || null)

const circleSize = computed(() => Math.round(props.size * 1.8))

const wrapStyle = computed(() => (
  props.circle
    ? { width: `${circleSize.value}px`, height: `${circleSize.value}px` }
    : {}
))

const mainStyle = computed(() => ({
  fontSize: `${props.size}px`,
  color: props.color
}))
</script>

<style scoped>
.device-icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.device-icon.with-circle {
  border-radius: 50%;
  background: var(--ion-color-light, #f3f4f6);
}
</style>
