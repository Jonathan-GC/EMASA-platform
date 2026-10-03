<template>
  <ion-page>
    <ion-header class="form-header-sticky ion-no-border">
      <ion-toolbar>
        <ion-title>Crear backup</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeModal">
            <ion-icon :icon="icons.close" slot="icon-only"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-card-content>
        <form @submit.prevent="createBackup">
          <ion-list>
            <ion-item class="custom">
              <ion-label position="stacked" class="!mb-2">Notas (opcional)</ion-label>
              <ion-textarea
                v-model="notes"
                class="custom"
                fill="solid"
                rows="4"
                placeholder="Ej: Pre-deployment v2.4.0"
              ></ion-textarea>
            </ion-item>
          </ion-list>
        </form>
      </ion-card-content>
    </ion-content>

    <ion-footer class="form-footer-sticky ion-no-border">
      <ion-toolbar>
        <div class="ion-text-end ion-padding">
          <ion-button type="submit" @click="createBackup" :disabled="loading">
            <ion-spinner v-if="loading" slot="start"></ion-spinner>
            Crear backup
          </ion-button>
        </div>
      </ion-toolbar>
    </ion-footer>
  </ion-page>
</template>

<script setup>
import { ref, inject } from 'vue'
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonIcon,
  IonContent,
  IonCardContent,
  IonList,
  IonItem,
  IonLabel,
  IonTextarea,
  IonFooter,
  IonSpinner,
} from '@ionic/vue'
import API from '@/utils/api/api'

const emit = defineEmits(['itemCreated', 'loaded', 'closed'])
const icons = inject('icons', {})

const notes = ref('')
const loading = ref(false)

const closeModal = () => {
  emit('closed')
}

const createBackup = async () => {
  loading.value = true
  try {
    const data = {}
    if (notes.value.trim()) data.notes = notes.value.trim()
    await API.post(API.BACKUPS, data)
    emit('itemCreated')
    closeModal()
  } catch (error) {
    console.error('Error creating backup:', error)
  } finally {
    loading.value = false
  }
}
</script>
