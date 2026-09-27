<template>
  <ion-page>
    <ion-header class="custom">
      <ion-toolbar>
        <ion-title>{{ isEdit ? 'Editar miembro de soporte' : 'Nuevo miembro de soporte' }}</ion-title>
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
        <p>Cargando datos...</p>
      </div>

      <div v-else-if="loadError" class="error-container ion-text-center">
        <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
        <p>{{ loadError }}</p>
        <ion-button @click="init" fill="outline">Reintentar</ion-button>
      </div>

      <div v-else>
        <ion-item v-if="!isEdit">
          <ion-label position="stacked">Usuario</ion-label>
          <ion-select
            v-model="userId"
            :placeholder="users.length ? 'Selecciona un usuario' : 'No hay usuarios disponibles'"
            :disabled="!users.length || submitting"
          >
            <ion-select-option v-for="u in users" :key="u.id" :value="u.id">
              {{ userLabel(u) }}
            </ion-select-option>
          </ion-select>
        </ion-item>

        <ion-item>
          <ion-label position="stacked">Rol</ion-label>
          <ion-select
            v-model="role"
            placeholder="Selecciona un rol"
            :disabled="submitting"
          >
            <ion-select-option v-for="(label, value) in roleOptions" :key="value" :value="value">
              {{ label }}
            </ion-select-option>
          </ion-select>
        </ion-item>

        <ion-item>
          <ion-label position="stacked">Alcance</ion-label>
          <ion-select
            v-model="scope"
            placeholder="Selecciona un alcance"
            :disabled="submitting"
          >
            <ion-select-option :value="GLOBAL_SCOPE">Global (sin tenant)</ion-select-option>
            <ion-select-option v-for="t in tenants" :key="t.id" :value="t.id">
              {{ t.name || `#${t.id}` }}
            </ion-select-option>
          </ion-select>
        </ion-item>

        <div class="ion-padding-top">
          <ion-button
            expand="block"
            :disabled="!canSubmit || submitting"
            @click="confirmSubmit"
            color="primary"
          >
            <ion-spinner v-if="submitting" name="crescent" slot="start"></ion-spinner>
            <ion-icon v-else :icon="icons.checkmark" slot="start"></ion-icon>
            {{ isEdit ? 'Guardar cambios' : 'Crear miembro' }}
          </ion-button>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import {
  IonPage, IonHeader, IonToolbar, IonTitle, IonContent,
  IonButtons, IonButton, IonIcon, IonItem, IonLabel,
  IonSelect, IonSelectOption, IonSpinner,
  alertController, toastController, modalController
} from '@ionic/vue'
import { close, checkmark, alertCircle } from 'ionicons/icons'
import API from '@utils/api/api'

const props = defineProps({
  mode: {
    type: String,
    default: 'create'
  },
  initialData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['itemCreated', 'itemEdited', 'closed'])

const GLOBAL_SCOPE = '__global__'

const icons = { ...{ close, checkmark, alertCircle }, ...inject('icons', {}) }

const roleOptions = {
  support_agent: 'Agente de Soporte',
  support_manager: 'Gestor de Soporte',
  technician: 'Técnico',
  other: 'Otro'
}

const users = ref([])
const tenants = ref([])
const loading = ref(true)
const loadError = ref('')
const submitting = ref(false)

const userId = ref(null)
const role = ref(null)
const scope = ref(GLOBAL_SCOPE)

const isEdit = computed(() => props.mode === 'edit')

const canSubmit = computed(() => {
  if (!role.value) return false
  if (!isEdit.value && !userId.value) return false
  return true
})

const toList = (res) => Array.isArray(res) ? res : (res?.results || res?.data || [])

const userLabel = (u) => {
  const name = [u.name, u.last_name].filter(Boolean).join(' ').trim()
  return name || u.username || u.email || `#${u.id}`
}

const fetchUsers = async () => {
  const res = await API.get(API.USER)
  users.value = toList(res)
}

const fetchTenants = async () => {
  const res = await API.get(API.TENANT)
  tenants.value = toList(res)
}

const init = async () => {
  loading.value = true
  loadError.value = ''
  try {
    await Promise.all([fetchUsers(), fetchTenants()])
    if (isEdit.value && props.initialData) {
      role.value = props.initialData.role || null
      scope.value = props.initialData.tenant ? String(props.initialData.tenant) : GLOBAL_SCOPE
    }
  } catch (err) {
    console.error('Error cargando datos del formulario de soporte:', err)
    loadError.value = 'No se pudieron cargar los datos necesarios.'
  } finally {
    loading.value = false
  }
}

const showToast = async (message, color = 'success') => {
  const toast = await toastController.create({
    message,
    duration: 3000,
    color,
    position: 'top'
  })
  await toast.present()
}

const confirmSubmit = async () => {
  const alert = await alertController.create({
    header: isEdit.value ? 'Guardar cambios' : 'Crear miembro de soporte',
    message: isEdit.value
      ? '¿Deseas guardar los cambios de este miembro de soporte?'
      : '¿Deseas agregar este usuario al equipo de soporte?',
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: isEdit.value ? 'Guardar' : 'Crear',
        role: 'confirm',
        handler: () => { submit() }
      }
    ]
  })
  await alert.present()
}

const submit = async () => {
  submitting.value = true
  try {
    const payload = { role: role.value }
    if (!isEdit.value) payload.user = userId.value
    if (scope.value === GLOBAL_SCOPE) {
      payload.tenant = null
    } else {
      payload.tenant = String(scope.value)
    }

    if (isEdit.value) {
      await API.patch(API.SUPPORT_MEMBERSHIP_DETAIL(props.initialData.id), payload)
      await showToast('Miembro de soporte actualizado exitosamente.')
      modalController.dismiss({ edited: true })
      emit('itemEdited')
    } else {
      await API.post(API.SUPPORT_MEMBERSHIP, payload)
      await showToast('Miembro de soporte creado exitosamente.')
      modalController.dismiss({ created: true })
      emit('itemCreated')
    }
  } catch (err) {
    console.error('Error guardando miembro de soporte:', err)
    await showToast(err.message || 'Error al guardar el miembro de soporte.', 'danger')
  } finally {
    submitting.value = false
  }
}

const closeModal = () => {
  modalController.dismiss()
  emit('closed')
}

onMounted(() => {
  init()
})
</script>

<style scoped>
.error-container {
  margin-top: 40px;
}

.error-container ion-icon {
  font-size: 64px;
  opacity: 0.5;
}
</style>