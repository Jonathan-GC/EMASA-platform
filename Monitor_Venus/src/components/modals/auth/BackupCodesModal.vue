<template>
  <ion-modal
    :is-open="isOpen"
    :backdrop-dismiss="false"
    :can-dismiss="canDismiss"
    @will-dismiss="onWillDismiss"
    @did-dismiss="onDidDismiss"
  >
    <ion-header class="custom">
      <ion-toolbar>
        <ion-title>Códigos de recuperación</ion-title>
        <ion-buttons slot="end">
          <ion-button
            class="back-button"
            text="Cerrar"
            :disabled="!acknowledged"
            @click="finish"
          ></ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content>
      <div class="backup-content">
        <div class="warn-box">
          <ion-icon :icon="icons.warning" class="warn-icon"></ion-icon>
          <div>
            <strong>Guárdalos ahora.</strong>
            <p class="warn-text">
              Cada código sirve una sola vez para entrar si pierdes el acceso a tu
              aplicación de autenticación. <strong>No volveremos a mostrarlos</strong>,
              así que cópialos o descárgalos antes de continuar.
            </p>
          </div>
        </div>

        <div class="codes-grid">
          <div v-for="(code, index) in codes" :key="index" class="code-chip">
            <span class="code-index">{{ index + 1 }}</span>
            <code class="code-value">{{ code }}</code>
          </div>
        </div>

        <div class="action-row">
          <ion-button
            expand="block"
            fill="outline"
            class="action-btn"
            @click="copyAll"
          >
            <ion-icon :icon="copied ? icons.checkmark : icons.copy" slot="start"></ion-icon>
            {{ copied ? '¡Copiado!' : 'Copiar todos' }}
          </ion-button>

          <ion-button
            expand="block"
            fill="outline"
            class="action-btn"
            @click="download"
          >
            <ion-icon :icon="icons.download" slot="start"></ion-icon>
            Descargar TXT
          </ion-button>
        </div>

        <ion-checkbox
          :checked="acknowledged"
          label-placement="end"
          justify="start"
          class="ack-check"
          @ionChange="onAckChange"
        >
          Ya guardé mis códigos en un lugar seguro
        </ion-checkbox>

        <ion-button
          expand="block"
          class="action-btn finish-btn"
          :disabled="!acknowledged"
          @click="finish"
        >
          Entendido
        </ion-button>
      </div>
    </ion-content>
  </ion-modal>
</template>

<script setup>
import { ref, watch, computed, inject } from 'vue'
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButton,
  IonButtons,
  IonIcon,
  IonContent,
  IonCheckbox
} from '@ionic/vue'

// Iconos desde el plugin
const icons = inject('icons', {})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  codes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['closed'])

const acknowledged = ref(false)
const copied = ref(false)

// Solo se puede cerrar el modal tras reconocer los códigos
const canDismiss = computed(() => acknowledged.value)

const fileStamp = computed(() => new Date().toISOString().slice(0, 10))

const reset = () => {
  acknowledged.value = false
  copied.value = false
}

const copyAll = async () => {
  const text = props.codes.join('\n')
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2500)
  } catch (err) {
    console.warn('No se pudieron copiar los códigos:', err)
  }
}

const download = () => {
  const content = [
    'EMASA Monitor - Códigos de recuperación',
    `Generados: ${new Date().toLocaleString()}`,
    '',
    ...props.codes.map((code, i) => `${String(i + 1).padStart(2, '0')}. ${code}`),
    '',
    'Cada código es de un solo uso.',
    'No se vuelven a mostrar en la aplicación.'
  ].join('\n')

  try {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `emasa-monitor-codigos-recuperacion-${fileStamp.value}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('No se pudo descargar el archivo:', err)
  }
}

const onAckChange = (e) => {
  acknowledged.value = !!e?.detail?.checked
}

const finish = () => {
  emit('closed')
}

// Los códigos solo se muestran una vez: no se permite cerrar sin reconocerlos.
// Ionic dispara este evento también con el botón físico del móvil.
const onWillDismiss = (ev) => {
  if (acknowledged.value) return
  ev.preventDefault()
  ev.detail?.register?.((dismiss) => {
    if (acknowledged.value) dismiss()
  })
}

const onDidDismiss = () => {
  emit('closed')
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) reset()
  }
)
</script>

<style scoped>
.backup-content {
  padding: 1.25rem 1.25rem 2rem;
  max-width: 480px;
  margin: 0 auto;
}

.warn-box {
  display: flex;
  gap: 0.65rem;
  align-items: flex-start;
  padding: 0.85rem;
  margin-bottom: 1.25rem;
  border-radius: 12px;
  background: rgba(245, 158, 11, 0.12);
  color: var(--color-zinc-800, #27272a);
}

.warn-icon {
  font-size: 1.35rem;
  flex-shrink: 0;
  color: #d97706;
}

.warn-text {
  margin: 0.25rem 0 0;
  font-size: 0.83rem;
  line-height: 1.45;
  color: var(--color-zinc-700, #3f3f46);
}

.codes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.code-chip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  background: rgba(113, 113, 122, 0.08);
  border: 1px solid rgba(113, 113, 122, 0.15);
}

.code-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--ion-color-primary, #2563eb);
  color: #fff;
  font-size: 0.68rem;
  font-weight: 600;
}

.code-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.85rem;
  letter-spacing: 0.08em;
}

.action-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.action-btn {
  --border-radius: 10px;
  min-height: 44px;
  text-transform: none;
  font-weight: 500;
}

.ack-check {
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.finish-btn {
  margin-bottom: 0.5rem;
}

.back-button {
  --color: var(--ion-color-medium);
  text-transform: none;
  font-size: 0.9rem;
}
</style>
