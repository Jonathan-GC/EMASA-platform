<template>
  <ion-page>
    <ion-header class="custom">
      <ion-toolbar>
        <ion-title>Usuarios con el rol: {{ role?.name }}</ion-title>
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
        <p>Cargando miembros...</p>
      </div>

      <div v-else-if="error" class="error-container ion-text-center">
        <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
        <p>{{ error }}</p>
        <ion-button @click="fetchMembers" fill="outline">Reintentar</ion-button>
      </div>

      <div v-else-if="members.length > 0">
        <ion-list>
          <ion-item v-for="member in members" :key="member.id">
            <ion-avatar slot="start">
              <img :src="formatImageUrl(member.img) || Avata"/>
            </ion-avatar>
            <ion-label>
              <h2>{{ member.name }} {{ member.last_name }}</h2>
              <p>{{ member.username }} | {{ member.email }}</p>
              <p v-if="member.tenant_name">
                <ion-badge color="primary">{{ member.tenant_name }}</ion-badge>
              </p>
            </ion-label>
            <ion-chip slot="end" :color="member.is_active ? 'success' : 'medium'">
              {{ member.is_active ? 'Activo' : 'Inactivo' }}
            </ion-chip>
            <ion-button 
              slot="end" 
              fill="clear" 
              color="secondary"
              shape="round"
              size="default"
              @click="handleRemoveUser(member)"
              :disabled="removingUserId === member.id"
            >
              <ion-icon 
                slot="icon-only" 
                :icon="removingUserId === member.id ? icons.hourglass : icons.error"
              ></ion-icon>
            </ion-button>
          </ion-item>
        </ion-list>
      </div>

      <div v-else class="empty-state ion-text-center ion-padding">
        <ion-icon :icon="icons.people" size="large" color="medium"></ion-icon>
        <h3>No hay usuarios</h3>
        <p>Este rol no tiene usuarios asignados actualmente.</p>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { 
  IonPage, IonHeader, IonToolbar, IonTitle, IonContent, 
  IonButtons, IonButton, IonIcon, IonList, IonItem, 
  IonLabel, IonAvatar, IonBadge, IonSpinner, modalController,
  alertController, toastController
} from '@ionic/vue'
import API from '@utils/api/api'
import Avatar from '@assets/svg/avatar.svg'

const props = defineProps({
  role: {
    type: Object,
    required: true
  }
})

const icons = inject('icons', {})
const members = ref([])
const loading = ref(true)
const error = ref(null)
const removingUserId = ref(null)

/**
 * Formats the image URL to include the backend base URL if it's a relative path.
 * Similar approach to authStore.js for consistent image loading.
 */
const formatImageUrl = (img) => {
  if (!img) return Avatar;
  
  // If it's already a full URL, return it
  if (img.startsWith('http://') || img.startsWith('https://')) {
    return img;
  }
  
  // If it's a relative path, prepend the backend URL
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/';
  // Remove '/api/' from the end to get the backend base URL
  const backendUrl = apiBaseUrl.replace(/\/api\/?$/, '');
  
  // Ensure the image path starts with /
  const imagePath = img.startsWith('/') ? img : `/${img}`;
  
  return `${backendUrl}${imagePath}`;
};

const fetchMembers = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await API.get(API.ROLE_MEMBERSHIP(props.role.id))
    members.value = Array.isArray(response) ? response : (response?.data || [])
  } catch (err) {
    console.error('Error fetching role members:', err)
    error.value = 'No se pudieron cargar los miembros del rol.'
  } finally {
    loading.value = false
  }
}

const handleRemoveUser = async (member) => {
  const alert = await alertController.create({
    header: 'Confirmar eliminación',
    message: `¿Estás seguro de que deseas remover a ${member.name} ${member.last_name} de este rol?`,
    buttons: [
      {
        text: 'Cancelar',
        role: 'cancel'
      },
      {
        text: 'Remover',
        role: 'confirm',
        handler: () => {
          removeUserFromRole(member.id)
        }
      }
    ]
  })

  await alert.present()
}

const removeUserFromRole = async (userId) => {
  removingUserId.value = userId
  try {
    await API.post(API.ROLE_REMOVE_USER(props.role.id), {
      user_id: userId
    })

    // Show success toast
    const toast = await toastController.create({
      message: 'Usuario removido del rol exitosamente',
      duration: 3000,
      color: 'success',
      position: 'top'
    })
    await toast.present()

    // Refresh the members list
    await fetchMembers()
  } catch (err) {
    console.error('Error removing user from role:', err)
    
    // Show error toast
    const toast = await toastController.create({
      message: err.message || 'Error al remover el usuario del rol',
      duration: 4000,
      color: 'danger',
      position: 'top'
    })
    await toast.present()
  } finally {
    removingUserId.value = null
  }
}


const closeModal = () => {
  modalController.dismiss()
}

onMounted(() => {
  fetchMembers()
})
</script>

<style scoped>
.error-container, .empty-state {
  margin-top: 40px;
}
.empty-state ion-icon {
  font-size: 64px;
  opacity: 0.5;
}
</style>
