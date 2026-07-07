<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Asignar Usuario a Workspace</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeModal">
            <ion-icon :icon="icons.close"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    
    <ion-content class="ion-padding">
      <ion-card>
        <ion-card-content>
          <form @submit.prevent="handleSubmit">
            <!-- Workspace Selector -->
            <div class="form-group">
                <ion-item class="custom">
              <ion-label class="form-label" position="stacked">
                <ion-icon :icon="icons.business"></ion-icon>
                Workspace *
              </ion-label>
              <ModalSelector
                v-model="formData.workspace_id"
                :options="workspaces"
                title="Seleccionar Workspace"
                placeholder="Seleccionar workspace..."
                display-field="name"
                value-field="id"
                :searchable="true"
                :search-fields="['name']"
                search-placeholder="Buscar workspace..."
              >
              
                <template #display="{ selected }">
                  <div v-if="selected" class="selector-display">
                    <ion-icon :icon="icons.business"></ion-icon>
                    <span>{{ selected.name }}</span>
                  </div>
                  <span v-else class="placeholder-text">Seleccionar workspace...</span>
                </template>
                <template #option="{ option }">
                  <div class="option-content">
                    <ion-icon :icon="icons.business"></ion-icon>
                    <div>
                      <div class="option-title">{{ option.name }}</div>
                      <div class="option-subtitle" v-if="option.tenant">
                        Tenant: {{ option.tenant.name }}
                      </div>
                    </div>
                  </div>
                </template>
              </ModalSelector>
              </ion-item>
            </div>

            <!-- User Selector -->
            <div class="form-group">
                <ion-item  class="custom">
              <ion-label class="form-label" position="stacked">
                <ion-icon :icon="icons.person"></ion-icon>
                Usuario *
              </ion-label>
              <ModalSelector
                v-model="formData.user_id"
                :options="users"
                title="Seleccionar Usuario"
                placeholder="Seleccionar usuario..."
                :display-field="getUserDisplay"
                value-field="id"
                :searchable="true"
                :search-fields="['first_name', 'last_name', 'email']"
                search-placeholder="Buscar usuario..."
              >
                <template #display="{ selected }">
                  <div v-if="selected" class="selector-display">
                    <ion-icon :icon="icons.person"></ion-icon>
                    <span>{{ getUserDisplay(selected) }}</span>
                  </div>
                  <span v-else class="placeholder-text">Seleccionar usuario...</span>
                </template>
                <template #option="{ option }">
                  <div class="option-content">
                    <ion-icon :icon="icons.person"></ion-icon>
                    <div>
                      <div class="option-title">{{ getUserDisplay(option) }}</div>
                      <div class="option-subtitle">{{ option.email }}</div>
                    </div>
                  </div>
                </template>
              </ModalSelector>
                </ion-item>
            </div>

            <!-- Role Display (Read-only if provided) -->
            <div class="form-group" v-if="selectedRole">
              <label class="form-label">
                <ion-icon :icon="icons.shield"></ion-icon>
                Rol
              </label>
              <div class="readonly-field">
                <div class="selector-display">
                  <div 
                    class="role-color-indicator"
                    :style="{ backgroundColor: selectedRole.color || '#5865F2' }"
                  ></div>
                  <div>
                    <div class="readonly-title">{{ selectedRole.name }}</div>
                    <div class="readonly-subtitle" v-if="selectedRole.description">
                      {{ selectedRole.description }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="loadingData" class="loading-state">
              <ion-spinner></ion-spinner>
              <p>Cargando datos...</p>
            </div>

            <!-- Error Message -->
            <ion-item v-if="error" lines="none" class="error-message">
              <ion-icon :icon="icons.alertCircle" slot="start" color="danger"></ion-icon>
              <ion-label color="danger">{{ error }}</ion-label>
            </ion-item>

            <!-- Action Buttons -->
            <div class="form-actions">
              <ion-button 
                fill="outline" 
                @click="closeModal"
                :disabled="submitting"
              >
                Cancelar
              </ion-button>
              <ion-button 
                type="submit"
                :disabled="!isFormValid || submitting || loadingData"
                color="primary"
              >
                <ion-spinner v-if="submitting" slot="start"></ion-spinner>
                {{ submitting ? 'Guardando...' : 'Asignar Usuario' }}
              </ion-button>
            </div>
          </form>
        </ion-card-content>
      </ion-card>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonIcon,
  IonContent,
  IonCard,
  IonCardContent,
  IonItem,
  IonLabel,
  IonSpinner
} from '@ionic/vue'
import ModalSelector from '@components/ui/ModalSelector.vue'
import API from '@utils/api/api'

const props = defineProps({
  initialData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['membershipCreated', 'closed'])

// Inject icons
const icons = inject('icons', {})

// Component state
const formData = ref({
  workspace_id: props.initialData.workspace_id || null,
  user_id: props.initialData.user_id || null,
  role_id: props.initialData.role_id || null
})

const workspaces = ref([])
const users = ref([])
const roles = ref([])
const selectedRole = ref(null)
const loadingData = ref(false)
const submitting = ref(false)
const error = ref(null)

// Computed
const isFormValid = computed(() => {
  return formData.value.workspace_id && 
         formData.value.user_id && 
         formData.value.role_id
})

// Methods
const getUserDisplay = (user) => {
  if (!user) return ''
  const firstName = user.name || ''
  const lastName = user.last_name || ''
  return `${firstName} ${lastName}`.trim() || user.email || 'Usuario sin nombre'
}

const fetchWorkspaces = async () => {
  try {
    console.log('🔄 Fetching workspaces...')
    const response = await API.get(API.WORKSPACE)
    workspaces.value = Array.isArray(response) ? response : (response?.data || [])
    console.log('✅ Workspaces loaded:', workspaces.value.length)
  } catch (err) {
    console.error('❌ Error fetching workspaces:', err)
    throw err
  }
}

const fetchUsers = async () => {
  try {
    console.log('🔄 Fetching users...')
    const response = await API.get(API.USER)
    users.value = Array.isArray(response) ? response : (response?.data || [])
    console.log('✅ Users loaded:', users.value.length)
  } catch (err) {
    console.error('❌ Error fetching users:', err)
    throw err
  }
}

const fetchRoles = async () => {
  try {
    console.log('🔄 Fetching roles...')
    const response = await API.get(API.ROLE)
    roles.value = Array.isArray(response) ? response : (response?.data || [])
    console.log('✅ Roles loaded:', roles.value.length)
    
    // If role_id is provided in initialData, find and set the selected role
    if (formData.value.role_id && roles.value.length > 0) {
      selectedRole.value = roles.value.find(r => r.id === formData.value.role_id)
      console.log('✅ Pre-selected role:', selectedRole.value?.name)
    }
  } catch (err) {
    console.error('❌ Error fetching roles:', err)
    throw err
  }
}

const loadAllData = async () => {
  loadingData.value = true
  error.value = null
  
  try {
    await Promise.all([
      fetchWorkspaces(),
      fetchUsers(),
      fetchRoles()
    ])
  } catch (err) {
    error.value = `Error al cargar datos: ${err.message}`
  } finally {
    loadingData.value = false
  }
}

const handleSubmit = async () => {
  if (!isFormValid.value) return
  
  submitting.value = true
  error.value = null
  
  try {
    console.log('📤 Submitting workspace membership:', formData.value)
    
    const response = await API.post(API.WORKSPACE_MEMBERSHIP, formData.value)
    
    console.log('✅ Workspace membership created:', response)
    emit('membershipCreated', response)
    closeModal()
  } catch (err) {
    console.error('❌ Error creating workspace membership:', err)
    error.value = `Error al asignar usuario: ${err.message}`
  } finally {
    submitting.value = false
  }
}

const closeModal = async () => {
  const { modalController } = await import('@ionic/vue')
  await modalController.dismiss()
}

// Lifecycle
onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--ion-color-dark);
  font-size: 0.95rem;
}

.selector-display {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ion-color-dark);
}

.placeholder-text {
  color: var(--ion-color-medium);
}

.option-content {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.option-title {
  font-weight: 500;
  color: var(--ion-color-dark);
}

.option-subtitle {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
  margin-top: 2px;
}

.role-color-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.readonly-field {
  padding: 12px;
  background-color: var(--ion-color-light);
  border-radius: 8px;
  border: 1px solid var(--ion-color-medium-tint);
}

.readonly-title {
  font-weight: 600;
  color: var(--ion-color-dark);
  margin-bottom: 4px;
}

.readonly-subtitle {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
}

.loading-state {
  text-align: center;
  padding: 20px;
  color: var(--ion-color-medium);
}

.loading-state ion-spinner {
  margin-bottom: 8px;
}

.error-message {
  margin: 16px 0;
  --background: var(--ion-color-danger-tint);
  --border-radius: 8px;
  padding: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--ion-color-light);
}
</style>
