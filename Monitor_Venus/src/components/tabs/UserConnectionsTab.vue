<template>
  <div class="content-card">
    <h3 class="content-card-title">
      <ion-icon :icon="icons.link"></ion-icon>
      Conexiones Disponibles
    </h3>
    <div class="connection-list">
      <div class="connection-item">
        <div class="connection-info">
          <svg viewBox="0 0 48 48" width="24" height="24" aria-hidden="true">
            <path fill="#EA4335"
              d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
            <path fill="#4285F4"
              d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
            <path fill="#FBBC05"
              d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
            <path fill="#34A853"
              d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
          </svg>
          <div class="connection-text">
            <span class="connection-name">Google</span>
            <ion-chip v-if="hasGoogleLinked" color="success" size="small" class="google-email-chip">
              {{ googleEmail }}
            </ion-chip>
          </div>
        </div>
        <div class="connection-toggle">
          <ion-toggle :checked="googleToggleEnabled" @ionChange="handleGoogleToggle"
            :disabled="googleToggleLoading"></ion-toggle>
        </div>
      </div>
    </div>
    <p v-if="linkError" class="link-error">{{ linkError }}</p>
  </div>

  <!-- Google Link Modal -->
  <ion-modal :is-open="isLinkModalOpen" @did-dismiss="handleLinkModalDismiss" class="google-link-modal">
    <ion-header class="custom">
      <ion-toolbar>
        <ion-title>Vincular Google</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeLinkModal">
            <ion-icon :icon="icons.close"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <div class="google-link-modal-content">
      <svg viewBox="0 0 48 48" width="48" height="48" aria-hidden="true">
        <path fill="#EA4335"
          d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
        <path fill="#4285F4"
          d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
        <path fill="#FBBC05"
          d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
        <path fill="#34A853"
          d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
      </svg>
      <p class="modal-description">
        Vincula tu cuenta de Google para acceder de forma rápida y segura, sin necesidad de contraseña.
      </p>
      <GoogleLoginButton mode="link" :next="`/users/${userId}`" @started="handleLinkStarted" />
    </div>
  </ion-modal>

  <!-- Google Unlink Confirmation Modal -->
  <ion-modal :is-open="isUnlinkModalOpen" @did-dismiss="closeUnlinkModal" class="google-link-modal">
    <ion-header class="custom">
      <ion-toolbar>
        <ion-title>Desvincular Google</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeUnlinkModal">
            <ion-icon :icon="icons.close"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <div class="google-link-modal-content">
      <div class="unlink-icon">
        <ion-icon :icon="icons.link" size="large" color="medium"></ion-icon>
      </div>
      <p class="modal-description">
        ¿Seguro que deseas desvincular tu cuenta de Google? Podrás volver a vincularla cuando quieras y
        seguirás accediendo con tu correo y contraseña.
      </p>
      <div class="modal-actions">
        <ion-button fill="outline" @click="closeUnlinkModal">Cancelar</ion-button>
        <ion-button color="danger" :disabled="googleUnlinkLoading" @click="confirmGoogleUnlink">
          <ion-spinner v-if="googleUnlinkLoading" name="crescent" slot="start"></ion-spinner>
          Desvincular
        </ion-button>
      </div>
    </div>
  </ion-modal>
</template>

<script setup>
import { ref, computed, inject, onMounted, onBeforeUnmount } from 'vue'
import { toastController } from '@ionic/vue'
import API from '@/utils/api/api'
import { useAuthStore } from '@/stores/authStore'

const props = defineProps({
  userId: { type: String, required: true },
  isOwnProfile: { type: Boolean, default: false },
})

const authStore = useAuthStore()
const icons = inject('icons', {})

const googleToggleLoading = ref(false)
const isLinkModalOpen = ref(false)
const isUnlinkModalOpen = ref(false)
const googleUnlinkLoading = ref(false)
const linkError = ref(null)

const hasGoogleLinked = computed(() => {
  return authStore.googleLinked
})

// Optimistic override while the user is mid-interaction (between clicking the
// toggle and the modal resolving). null = no override (use store truth).
const userIntent = ref(null)

const googleToggleEnabled = computed(() =>
  userIntent.value !== null ? userIntent.value : authStore.googleLinked
)

const googleEmail = computed(() => authStore.googleEmail || '')

const handleGoogleToggle = async (ev) => {
  const checked = ev.detail.checked
  userIntent.value = checked
  if (checked && !hasGoogleLinked.value) {
    isLinkModalOpen.value = true
  } else if (!checked && hasGoogleLinked.value) {
    isUnlinkModalOpen.value = true
  }
}

const handleLinkModalDismiss = () => {
  userIntent.value = null
  isLinkModalOpen.value = false
}

const closeLinkModal = () => {
  userIntent.value = null
  isLinkModalOpen.value = false
}

const handleLinkStarted = () => {
  userIntent.value = null
  isLinkModalOpen.value = false
}

const closeUnlinkModal = () => {
  userIntent.value = null
  isUnlinkModalOpen.value = false
}

const confirmGoogleUnlink = async () => {
  googleUnlinkLoading.value = true
  try {
    await API.post(API.GOOGLE_UNLINK)
    await authStore.fetchUserProfile().catch(() => { })
    userIntent.value = null
    isUnlinkModalOpen.value = false
  } catch (err) {
    console.error('Error al desvincular Google:', err)
    userIntent.value = null
    const toast = await toastController.create({
      message: 'No se pudo desvincular la cuenta de Google. Inténtalo de nuevo.',
      duration: 4000,
      color: 'danger',
      position: 'top'
    })
    await toast.present()
  } finally {
    googleUnlinkLoading.value = false
  }
}

const refreshOwnProfile = () => {
  if (!props.isOwnProfile) return
  authStore.fetchUserProfile().catch(() => { })
}

onMounted(() => {
  refreshOwnProfile()
  window.addEventListener('google-account-linked', handleLinked)
  window.addEventListener('google-account-linked-error', handleLinkError)
})

onBeforeUnmount(() => {
  window.removeEventListener('google-account-linked', handleLinked)
  window.removeEventListener('google-account-linked-error', handleLinkError)
})

const handleLinked = () => {
  linkError.value = null
  refreshOwnProfile()
}

const handleLinkError = (ev) => {
  linkError.value = ev?.detail?.message || 'No se pudo vincular la cuenta de Google.'
  refreshOwnProfile()
}
</script>

<style scoped>
.content-card {
  box-sizing: border-box;
  width: 100%;
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.content-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: var(--ion-text-color);
}

.connection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.connection-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 8px;
}

.connection-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.connection-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.connection-name {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--ion-text-color);
}

.google-email-chip {
  align-self: flex-start;
  margin: 4px 0 0;
}

.connection-toggle {
  flex-shrink: 0;
}

.link-error {
  color: #c0392b;
  font-size: 0.9rem;
  margin: 10px 0 0;
}

.google-link-modal {
  --width: 340px;
  --height: auto;
  --max-height: 90vh;
  --border-radius: 16px;
}

.google-link-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 200px;
  padding: 24px 32px 32px;
  text-align: center;
}

.modal-description {
  margin: 0;
  font-size: 0.95rem;
  color: var(--ion-color-medium);
  line-height: 1.5;
  max-width: 280px;
}

.unlink-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--ion-color-light, #f3f4f6);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .content-card {
    padding: 16px;
  }
}
</style>
