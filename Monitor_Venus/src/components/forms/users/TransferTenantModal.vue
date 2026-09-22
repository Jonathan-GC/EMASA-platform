<template>
  <ion-page>
    <ion-header class="custom">
      <ion-toolbar>
        <ion-title>Transferir de tenant</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeModal">
            <ion-icon :icon="icons.close"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <div v-if="loading" class="ion-text-center ion-padding">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando tenants disponibles...</p>
      </div>

      <div v-else-if="error" class="error-container ion-text-center">
        <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
        <p>{{ error }}</p>
        <ion-button @click="fetchTenants" fill="outline">Reintentar</ion-button>
      </div>

      <div v-else>
        <ion-item class="user-summary" lines="none">
          <ion-avatar slot="start">
            <img :src="formatImageUrl(user.img) || Avatar" alt="avatar" />
          </ion-avatar>
          <ion-label>
            <h2>{{ user.name }} {{ user.last_name }}</h2>
            <p>{{ user.username }}</p>
            <ion-chip size="small" color="primary">
              <ion-icon :icon="icons.business"></ion-icon>
              {{ user.tenant_name || 'Sin tenant' }}
            </ion-chip>
          </ion-label>
        </ion-item>

        <ion-note color="warning" class="warning-note">
          <ion-icon :icon="icons.warning"></ion-icon>
          Al transferir al usuario se eliminarán sus membresías de workspace, roles y permisos actuales. El usuario será asignado al workspace por defecto con el rol "Sin rol".
        </ion-note>

        <ion-item>
          <ion-label position="stacked">Tenant de destino</ion-label>
          <ion-select
            :placeholder="!tenants.length ? 'No hay tenants disponibles' : 'Selecciona un tenant'"
            v-model="destinationTenantId"
            :disabled="!tenants.length"
          >
            <ion-select-option
              v-for="tenant in tenants"
              :key="tenant.id"
              :value="tenant.id"
            >
              {{ tenant.name }} <template v-if="tenant.is_global">(Global)</template>
            </ion-select-option>
          </ion-select>
        </ion-item>

        <div class="ion-padding-top">
          <ion-button
            expand="block"
            :disabled="!destinationTenantId || transferring"
            @click="confirmTransfer"
            color="primary"
          >
            <ion-spinner v-if="transferring" name="crescent" slot="start"></ion-spinner>
            <ion-icon v-else :icon="icons['swap-horizontal']" slot="start"></ion-icon>
            Transferir usuario
          </ion-button>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import {
  IonPage, IonHeader, IonToolbar, IonTitle, IonContent,
  IonButtons, IonButton, IonIcon, IonItem, IonLabel, IonNote,
  IonAvatar, IonChip, IonSelect, IonSelectOption, IonSpinner,
  alertController, toastController, modalController
} from '@ionic/vue'
import API from '@utils/api/api'
import Avatar from '@assets/svg/Avatar.svg'

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
})

const icons = inject('icons', {})
const tenants = ref([])
const destinationTenantId = ref(null)
const loading = ref(true)
const transferring = ref(false)
const error = ref(null)

const formatImageUrl = (img) => {
  if (!img) return null
  if (img.startsWith('http://') || img.startsWith('https://')) {
    return img
  }
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/'
  const backendUrl = apiBaseUrl.replace(/\/api\/?$/, '')
  const imagePath = img.startsWith('/') ? img : `/${img}`
  return `${backendUrl}${imagePath}`
}

const fetchTenants = async () => {
  loading.value = true
  error.value = null
  try {
    // Sin X-Tenant-ID para obtener todos los tenants disponibles como destino
    const response = await API.get(API.TENANT, { 'X-Tenant-ID': '' })
    const data = Array.isArray(response) ? response : (response?.data || [])
    tenants.value = data.filter(t => String(t.id) !== String(props.user.tenant))
  } catch (err) {
    console.error('Error fetching tenants:', err)
    error.value = 'No se pudieron cargar los tenants disponibles.'
  } finally {
    loading.value = false
  }
}

const confirmTransfer = async () => {
  const alert = await alertController.create({
    header: 'Confirmar transferencia',
    message: `¿Estás seguro de que deseas transferir a ${props.user.name} ${props.user.last_name} a otro tenant? Esta acción reinicia sus roles y permisos.`,
    buttons: [
      {
        text: 'Cancelar',
        role: 'cancel'
      },
      {
        text: 'Transferir',
        role: 'confirm',
        handler: () => {
          transferUser()
        }
      }
    ]
  })
  await alert.present()
}

const transferUser = async () => {
  transferring.value = true
  try {
    await API.post(API.TRANSFER_TENANT(props.user.id), {
      destination_tenant_id: destinationTenantId.value
    })

    const toast = await toastController.create({
      message: `Usuario transferido exitosamente a ${tenants.value.find(t => String(t.id) === String(destinationTenantId.value))?.name || 'nuevo tenant'}`,
      duration: 3000,
      color: 'success',
      position: 'top'
    })
    await toast.present()

    modalController.dismiss({ transferred: true })
  } catch (err) {
    console.error('Error transferring user:', err)

    const toast = await toastController.create({
      message: err.message || 'Error al transferir el usuario',
      duration: 4000,
      color: 'danger',
      position: 'top'
    })
    await toast.present()
  } finally {
    transferring.value = false
  }
}

const closeModal = () => {
  modalController.dismiss()
}

onMounted(() => {
  fetchTenants()
})
</script>

<style scoped>
.user-summary {
  margin-bottom: 12px;
}

.warning-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  background: var(--ion-color-warning-tint, #fff6e6);
  margin-bottom: 12px;
  white-space: normal;
}

.error-container {
  margin-top: 40px;
}

.error-container ion-icon {
  font-size: 64px;
  opacity: 0.5;
}
</style>