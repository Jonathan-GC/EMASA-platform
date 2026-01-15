<template>
  <ion-page>
    <ion-header class="form-header-sticky ion-no-border">
      <ion-toolbar>
        <ion-title>Actualizar Rol</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeModal">
            <ion-icon :icon="icons.close" slot="icon-only"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <!-- Loading state -->
      <div v-if="!loaded" class="loading-container">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando formulario...</p>
      </div>

      <!-- Form content -->
      <ion-card-content v-else class="role-form-container">
        <form @submit.prevent="createRole">
          <!-- Role Preview Section -->
          <div class="role-preview-section">
            <h3>Vista Previa</h3>
            <div 
              class="role-preview-card"
              :style="{ 
                background: `linear-gradient(135deg, var(--ion-color-light-tint) 0%, ${formValues.color}10 100%)` 
              }"
            >
              <div class="role-badge-preview">
                <div 
                  class="role-color-circle" 
                  :style="{ backgroundColor: formValues.color }"
                ></div>
                <span 
                  class="role-name-preview"
                  :style="{ color: formValues.color }"
                >
                  {{ formValues.name || 'Nuevo Rol' }}
                </span>
              </div>
              <p class="role-description-preview">
                {{ formValues.description || 'Sin descripción' }}
              </p>
              <div class="role-members-preview">
                <ion-icon :icon="icons.people"></ion-icon>
                <span>0 miembros con este rol</span>
              </div>
            </div>
          </div>

          <!-- Basic Information Section -->
          <div class="form-section">
            <h3>Información Básica</h3>
            
            <ion-list class="custom">
              <ion-item class="custom">
                <ion-label position="stacked" class="!mb-2">Nombre del Rol</ion-label>
                <ion-input 
                  v-model="formValues.name" 
                  class="custom" 
                  fill="solid" 
                  placeholder="ej: Administrador, Moderador, Miembro"
                  required
                />
              </ion-item>

              <ion-item class="custom">
                <ion-label position="stacked" class="!mb-2">Descripción</ion-label>
                <ion-textarea 
                  v-model="formValues.description" 
                  class="custom" 
                  fill="solid" 
                  rows="3"
                  placeholder="Describe el propósito de este rol..."
                />
              </ion-item>

              <ion-item class="custom">
                <ion-label position="stacked" class="!mb-2">Workspace</ion-label>
                <ModalSelector
                  v-model="formValues.workspace_id"
                  :options="workspaces"
                  title="Seleccionar Workspace"
                  placeholder="Selecciona un workspace..."
                  display-field="name"
                  value-field="id"
                  :searchable="true"
                  search-placeholder="Buscar workspace..."
                  :search-fields="['name', 'description']"
                />
              </ion-item>
            </ion-list>
          </div>

          <!-- Color Selection Section -->
          <div class="form-section">
            <h3>Color del Rol</h3>
            <p class="section-description">
              Selecciona un color para identificar visualmente este rol
            </p>
            
            <div class="color-picker-container">
              <!-- Predefined color palette -->
              <div class="color-palette">
                <div 
                  v-for="color in predefinedColors" 
                  :key="color"
                  class="color-option"
                  :class="{ 'selected': formValues.color === color }"
                  :style="{ backgroundColor: color }"
                  @click="selectColor(color)"
                >
                  <ion-icon 
                    v-if="formValues.color === color"
                    :icon="icons.checkmark"
                    class="check-icon"
                  ></ion-icon>
                </div>
              </div>
              
              <!-- Custom color picker -->
              <div class="custom-color-picker">
                <ColorPicker
                  v-model="formValues.color"
                  label="Color Personalizado"
                  title="Seleccionar Color del Rol"
                  :show-palette="false"
                  :show-rgb="false"
                />
              </div>
            </div>
          </div>

          
        </form>
      </ion-card-content>
    </ion-content>
    
    <ion-footer class="form-footer-sticky ion-no-border">
      <ion-toolbar>
        <div class="form-actions">
          <ion-button 
            type="button" 
            fill="outline" 
            @click="closeModal"
            :disabled="loading"
          >
            Cancelar
          </ion-button>
          <ion-button 
            type="submit"
            @click="createRole"
            :disabled="loading || !formValues.name"
            color="primary"
          >
            <ion-spinner v-if="loading" slot="start"></ion-spinner>
            {{ loading ? 'Actualizando...' : 'Actualizar Rol' }}
          </ion-button>
        </div>
      </ion-toolbar>
    </ion-footer>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, inject, onMounted } from 'vue'
import {
  IonPage,
  IonHeader,
  IonFooter,
  IonContent,
  IonCard,
  IonCardContent,
  IonList,
  IonItem,
  IonLabel,
  IonInput,
  IonTextarea,
  IonCheckbox,
  IonButton,
  IonSpinner,
  IonIcon,
  IonToolbar,
  IonTitle,
  IonButtons
} from '@ionic/vue'
import API from '@utils/api/api'
import ModalSelector from '@/components/ui/ModalSelector.vue'
import ColorPicker from '@/components/ui/ColorPicker.vue'

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  index:{
    type: Number,
  },
  fields: {
    type: Array,
    default: () => [],
  },
  type: {
    type: String,
    required: true,
  },
  initialData: {
    type: Object,
    default: () => ({}),
  }
})

const emit = defineEmits(['itemEdited', 'closed'])

const icons = inject('icons', {})
const loading = ref(false)
const loaded = ref(false)
const workspaces = ref([])
const permissions = ref([])

// Form values
const formValues = ref({
  name: '',
  description: '',
  color: '#5865F2',
  workspace_id: null,
  permissions: {
    // General
    view_dashboard: false,
    view_analytics: false,
    manage_settings: false,
    
    // Management
    manage_users: false,
    manage_roles: false,
    manage_workspaces: false,
    manage_tenants: false,
    
    // Devices
    view_devices: false,
    create_devices: false,
    edit_devices: false,
    delete_devices: false,
    manage_gateways: false,
    view_measurements: false,
  }
})

// Discord-like predefined colors
const predefinedColors = [
  '#5865F2', // Blurple (Discord default)
  '#3498DB', // Blue
  '#2ECC71', // Green
  '#F1C40F', // Yellow
  '#E67E22', // Orange
  '#ED4245', // Red
  '#EB459E', // Pink
  '#99AAB5', // Grey
  '#23272A', // Dark
]

// Permission categories
const generalPermissions = [
  {
    key: 'view_dashboard',
    label: 'Ver Dashboard',
    description: 'Permite visualizar el panel principal',
    icon: icons.grid
  },
  {
    key: 'view_analytics',
    label: 'Ver Analíticas',
    description: 'Acceso a reportes y análisis',
    icon: icons.analytics
  },
  {
    key: 'manage_settings',
    label: 'Gestionar Configuración',
    description: 'Modificar configuraciones del sistema',
    icon: icons.settings
  },
]

const managementPermissions = [
  {
    key: 'manage_users',
    label: 'Gestionar Usuarios',
    description: 'Crear, editar y eliminar usuarios',
    icon: icons.people
  },
  {
    key: 'manage_roles',
    label: 'Gestionar Roles',
    description: 'Administrar roles y permisos',
    icon: icons.shield
  },
  {
    key: 'manage_workspaces',
    label: 'Gestionar Workspaces',
    description: 'Administrar espacios de trabajo',
    icon: icons.business
  },
  {
    key: 'manage_tenants',
    label: 'Gestionar Tenants',
    description: 'Administrar organizaciones',
    icon: icons.home
  },
]

const devicePermissions = [
  {
    key: 'view_devices',
    label: 'Ver Dispositivos',
    description: 'Visualizar lista de dispositivos',
    icon: icons.hardwareChip
  },
  {
    key: 'create_devices',
    label: 'Crear Dispositivos',
    description: 'Agregar nuevos dispositivos',
    icon: icons.add
  },
  {
    key: 'edit_devices',
    label: 'Editar Dispositivos',
    description: 'Modificar dispositivos existentes',
    icon: icons.create
  },
  {
    key: 'delete_devices',
    label: 'Eliminar Dispositivos',
    description: 'Remover dispositivos del sistema',
    icon: icons.trash
  },
  {
    key: 'manage_gateways',
    label: 'Gestionar Gateways',
    description: 'Administrar puertas de enlace',
    icon: icons.wifi
  },
  {
    key: 'view_measurements',
    label: 'Ver Mediciones',
    description: 'Acceder a datos de mediciones',
    icon: icons.pulse
  },
]

const selectColor = (color) => {
  formValues.value.color = color
}

const closeModal = () => {
  emit('closed')
}

const createRole = async () => {
  loading.value = true
  
  try {
    // Prepare payload
    const payload = {
      name: formValues.value.name,
      description: formValues.value.description,
      color: formValues.value.color,
      workspace_id: formValues.value.workspace_id,
      permissions: Object.keys(formValues.value.permissions)
        .filter(key => formValues.value.permissions[key])
    }

    console.log('📤 Creating role:', payload)
    
    const response = await API.patch(`${API.ROLE}${props.index}/`, payload)
    
    if (!response.error) {
      console.log('✅ Role updated successfully')
      emit('itemEdited', formValues.value.name)
      closeModal()
    }
  } catch (error) {
    console.error('❌ Error updating role:', error)
  } finally {
    loading.value = false
  }
}

const fetchWorkspaces = async () => {
  try {
    const response = await API.get(API.WORKSPACE)
    workspaces.value = Array.isArray(response) ? response : []
    console.log('✅ Workspaces loaded:', workspaces.value.length)
  } catch (error) {
    console.error('❌ Error fetching workspaces:', error)
    workspaces.value = []
  }
};

const fetchPermissions = async () => {
  // Placeholder for future permission fetching logic if needed
  try {
    const response = await API.get(API.ASSIGNABLE_PERMISSIONS(formValues.value.id))
    permissions.value = Array.isArray(response) ? response : []
  } catch (error) {
    c
    console.error('❌ Error fetching permissions:', error)
    permissions.value = []
  }
};

onMounted( async () => {
  await fetchWorkspaces();
  
  // Populate form with initialData if provided
  if (props.initialData && Object.keys(props.initialData).length > 0) {
    console.log('📝 Populating form with initial data:', props.initialData)
    
    formValues.value = {
      ...formValues.value,
      name: props.initialData.name || '',
      description: props.initialData.description || '',
      color: props.initialData.color || '#5865F2',
      workspace_id: props.initialData.workspace_id || null,
    }
  }
  
  loaded.value = true
  console.log('🎭 Role creation form mounted')
})
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.loading-container ion-spinner {
  margin-bottom: 16px;
}

.loading-container p {
  color: var(--ion-color-medium);
}

.role-form-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 1.5rem;
}

.divider {
  margin: 0;
  border: none;
  border-top: 1px solid var(--ion-color-light-shade);
}

.form-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--ion-color-light-tint);
  border-radius: 12px;
}

.form-section h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  color: var(--ion-color-dark);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-description {
  margin: 0 0 1rem 0;
  font-size: 0.9rem;
  color: var(--ion-color-medium);
}

/* Role Preview */
.role-preview-section {
  margin-bottom: 2rem;
}

.role-preview-card {
  padding: 1.5rem;
  border-radius: 12px;

  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.role-badge-preview {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.role-color-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid var(--ion-color-light);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.role-name-preview {
  font-size: 1.5rem;
  font-weight: 700;
}

.role-description-preview {
  margin: 0 0 1rem 0;
  font-size: 0.95rem;
  color: var(--ion-color-medium);
}

.role-members-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: var(--ion-color-medium);
}

/* Color Picker */
.color-picker-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.color-palette {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
  gap: 0.75rem;
}

.color-option {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid transparent;
  position: relative;
}

.color-option:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.color-option.selected {
  border-color: var(--ion-color-dark);
  box-shadow: 0 0 0 2px white, 0 0 0 4px var(--ion-color-dark);
}

.check-icon {
  font-size: 24px;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.color-input-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
}

.color-picker {
  width: 60px;
  height: 60px;
  border: 2px solid var(--ion-color-light-shade);
  border-radius: 8px;
  cursor: pointer;
}

.color-hex-input {
  flex: 1;
}

/* Permissions */
.permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.permission-category h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: var(--ion-color-dark);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 700;
}

.permission-item {
  --padding-start: 0;
  --inner-padding-end: 0;
  margin-bottom: 0.5rem;
}

.permission-info {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  flex: 1;
}

.permission-icon {
  font-size: 20px;
  color: var(--ion-color-primary);
  margin-top: 2px;
  flex-shrink: 0;
}

.permission-text {
  flex: 1;
}

.permission-text strong {
  display: block;
  font-size: 0.95rem;
  color: var(--ion-color-dark);
  margin-bottom: 0.25rem;
}

.permission-text p {
  margin: 0;
  font-size: 0.8rem;
  color: var(--ion-color-medium);
  line-height: 1.3;
}

/* Form Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 0.5rem 1rem;
  width: 100%;
}

/* Responsive */
@media (max-width: 768px) {
  .role-form-container {
    padding: 1rem;
  }

  .permissions-grid {
    grid-template-columns: 1fr;
  }

  .color-palette {
    grid-template-columns: repeat(6, 1fr);
  }

  .form-actions {
    flex-direction: column;
  }

  .form-actions ion-button {
    width: 100%;
  }
}
</style>
