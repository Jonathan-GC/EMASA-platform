<template>
  <ion-page v-if="loaded">
    <ion-content class="ion-padding">
      <ion-card-header class="custom">
        <ion-toolbar>
          <ion-title>
            <div class="title-with-role">
              <ion-icon :icon="icons.key"></ion-icon>
              <span>Permisos del Rol</span>
            </div>
          </ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeModal">
              <ion-icon :icon="icons.close" slot="icon-only"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-card-header>
      <hr class="divider" />
      
      <ion-card-content v-if='loaded' class="permissions-manager-container">
        <!-- Role Info Header -->
        <div class="role-info-header">
          <div class="role-badge">
            <div 
              class="role-color-circle" 
              :style="{ backgroundColor: role?.color || '#5865F2' }"
            ></div>
            <div class="role-details">
              <h2>{{ role?.name || 'Sin nombre' }}</h2>
              <p>{{ role?.description || 'Sin descripción' }}</p>
            </div>
          </div>
        </div>

        <!-- Permissions Section -->
        <div class="permissions-section">
          <!-- Loading state -->
          <div v-if="loadingPermissions" class="permissions-loading">
            <ion-spinner></ion-spinner>
            <p>Cargando permisos disponibles...</p>
          </div>

          <!-- No permissions available -->
          <div v-else-if="permissionCategories.length === 0" class="permissions-empty">
            <ion-icon :icon="icons.alertCircle" class="empty-icon"></ion-icon>
            <p>No hay permisos disponibles para este rol</p>
          </div>

          <!-- Dynamic permissions grid -->
          <div v-else class="permissions-container">
            <div 
              v-for="category in permissionCategories" 
              :key="category.key"
              class="permission-category-section"
            >
              <div class="category-header">
                <ion-icon :icon="category.icon" class="category-icon"></ion-icon>
                <h4>{{ category.label }}</h4>
                <span class="item-count">{{ category.items.length }} items</span>
              </div>

              <div class="permission-items">
                <div 
                  v-for="item in category.items" 
                  :key="item.id"
                  class="permission-item-card"
                >
                  <div class="item-name">
                    <strong>{{ item.name }}</strong>
                  </div>
                  <div class="item-permissions">
                    <ion-checkbox 
                      v-for="(value, permKey) in item.permissions" 
                      :key="permKey"
                      :checked="isPermissionChecked(category.key, item.id, permKey)"
                      @ionChange="(e) => togglePermission(category.key, item.id, permKey, e.detail.checked)"
                      class="permission-checkbox"
                    >
                      <span>
                        {{ permKey.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) }}
                      </span>
                    </ion-checkbox>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="form-actions">
          <ion-button 
            fill="outline" 
            @click="closeModal"
            :disabled="loading"
          >
            Cancelar
          </ion-button>
          <ion-button 
            @click="savePermissions"
            :disabled="loading || loadingPermissions"
            color="primary"
          >
            <ion-spinner v-if="loading" slot="start"></ion-spinner>
            {{ loading ? 'Guardando...' : 'Guardar Permisos' }}
          </ion-button>
        </div>
      </ion-card-content>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, inject, onMounted, computed } from 'vue'
import {
  IonPage,
  IonContent,
  IonCardContent,
  IonCheckbox,
  IonButton,
  IonSpinner,
  IonIcon,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonCardHeader
} from '@ionic/vue'
import API from '@utils/api/api'

const props = defineProps({
  role: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['permissionsUpdated', 'closed'])

const icons = inject('icons', {})
const loading = ref(false)
const loadingPermissions = ref(false)
const assignablePermissions = ref(null)
const permissions = ref({})
const loaded = ref(false)

// Computed property to get permission categories from API response
const permissionCategories = computed(() => {
  console.log('🔄 Computing permission categories...')
  console.log('📊 assignablePermissions.value:', assignablePermissions.value)
  
  if (!assignablePermissions.value?.object) {
    console.warn('⚠️ No object property found in assignablePermissions')
    return []
  }
  
  const categories = []
  const objectPerms = assignablePermissions.value.object
  
  console.log('📦 objectPerms keys:', Object.keys(objectPerms))
  
  // Map of category names to display labels
  const categoryLabels = {
    tenant: 'Tenants',
    workspace: 'Workspaces',
    device: 'Dispositivos',
    gateway: 'Gateways',
    application: 'Aplicaciones',
    machine: 'Máquinas',
    deviceprofile: 'Perfiles de Dispositivo',
    apiuser: 'Usuarios API',
    role: 'Roles',
    workspacemembership: 'Membresías'
  }
  
  // Map of category names to icons
  const categoryIcons = {
    tenant: icons.business,
    workspace: icons.briefcase,
    device: icons.hardwareChip,
    gateway: icons.wifi,
    application: icons.apps,
    machine: icons.construct,
    deviceprofile: icons.documentText,
    apiuser: icons.key,
    role: icons.shield,
    workspacemembership: icons.people
  }
  
  for (const [categoryKey, items] of Object.entries(objectPerms)) {
    console.log(`🔍 Processing category: ${categoryKey}, isArray: ${Array.isArray(items)}, length: ${items?.length}`)
    
    if (Array.isArray(items) && items.length > 0) {
      categories.push({
        key: categoryKey,
        label: categoryLabels[categoryKey] || categoryKey,
        icon: categoryIcons[categoryKey] || icons.ellipse,
        items: items
      })
      console.log(`✅ Added category: ${categoryKey} with ${items.length} items`)
    }
  }
  
  console.log('📋 Total categories computed:', categories.length)
  return categories
})

// Helper function to get permission key for an object
const getPermissionKey = (categoryKey, itemId, permissionType) => {
  return `${categoryKey}_${itemId}_${permissionType}`
}

// Helper to check if permission is checked
const isPermissionChecked = (categoryKey, itemId, permissionType) => {
  const key = getPermissionKey(categoryKey, itemId, permissionType)
  
  // If user has toggled this permission, use that value
  if (key in permissions.value) {
    return permissions.value[key]
  }
  
  // Otherwise, find the initial value from API response
  if (!assignablePermissions.value?.object) return false
  
  const categoryItems = assignablePermissions.value.object[categoryKey]
  if (!Array.isArray(categoryItems)) return false
  
  const item = categoryItems.find(i => i.id === itemId)
  if (!item || !item.permissions) return false
  
  // Return the API value (true if permission is assignable)
  return item.permissions[permissionType] === true
}

// Helper to toggle permission
const togglePermission = (categoryKey, itemId, permissionType, value) => {
  const key = getPermissionKey(categoryKey, itemId, permissionType)
  console.log(`🔄 Toggle: ${key} = ${value}`)
  permissions.value[key] = value
  console.log('📝 Current permissions state:', permissions.value)
}

const closeModal = async () => {
  const { modalController } = await import('@ionic/vue')
  await modalController.dismiss()
}

const fetchPermissions = async () => {
  if (!props.role?.id) {
    console.warn('⚠️ No role ID provided, skipping permission fetch')
    return
  }
  
  loadingPermissions.value = true
  try {
    console.log('🔍 Fetching assignable permissions for role:', props.role.id)
    let response = await API.get(API.ASSIGNABLE_PERMISSIONS(props.role.id))
    
    console.log('📦 Raw API response type:', Array.isArray(response) ? 'Array' : typeof response)
    
    // Handle array response - extract first element
    if (Array.isArray(response) && response.length > 0) {
      console.log('✅ Response is array, extracting first element')
      response = response[0]
    }
    
    console.log('📦 Response keys:', Object.keys(response || {}))
    
    // Handle nested structure: { assignable_permissions: { global: {}, object: {} } }
    if (response && response.assignable_permissions) {
      console.log('✅ Found assignable_permissions in response')
      assignablePermissions.value = response.assignable_permissions
    } else if (response && response.object) {
      console.log('✅ Found object directly in response')
      assignablePermissions.value = response
    } else {
      console.error('❌ Unexpected response structure:', response)
      assignablePermissions.value = { object: {} }
    }
    
    console.log('✅ Has object property:', !!assignablePermissions.value?.object)
    console.log('✅ Permissions loaded:', Object.keys(assignablePermissions.value?.object || {}).length, 'categories')
    console.log('🔑 Available categories:', Object.keys(assignablePermissions.value?.object || {}))
    
    // Initialize permissions state from API response
    initializePermissions()
  } catch (error) {
    console.error('❌ Error fetching permissions:', error)
    assignablePermissions.value = { object: {} }
  } finally {
    loadingPermissions.value = false
  }
}

const initializePermissions = () => {
  if (!assignablePermissions.value?.object) return
  
  const objectPerms = assignablePermissions.value.object
  
  // Initialize permissions with API values (true = assignable)
  for (const [categoryKey, items] of Object.entries(objectPerms)) {
    if (!Array.isArray(items)) continue
    
    for (const item of items) {
      if (!item.permissions) continue
      
      for (const [permKey, value] of Object.entries(item.permissions)) {
        if (value === true) {
          const key = getPermissionKey(categoryKey, item.id, permKey)
          permissions.value[key] = true
        }
      }
    }
  }
  
  console.log('✅ Initialized permissions:', Object.keys(permissions.value).length, 'permissions')
}

const savePermissions = async () => {
  loading.value = true
  
  try {
    // Build assign and revoke structures
    const assign = {}
    const revoke = {}
    
    if (!assignablePermissions.value?.object) {
      console.error('❌ No permissions data available')
      return
    }
    
    const objectPerms = assignablePermissions.value.object
    
    // Iterate through all categories and items
    for (const [categoryKey, items] of Object.entries(objectPerms)) {
      if (!Array.isArray(items)) continue
      
      console.log(`🔍 Processing category: ${categoryKey} with ${items.length} items`)
      
      for (const item of items) {
        if (!item.permissions) continue
        
        for (const [permKey, apiValue] of Object.entries(item.permissions)) {
          // Get current value using the same logic as the UI
          const currentValue = isPermissionChecked(categoryKey, item.id, permKey)
          const initialValue = apiValue === true
          
          console.log(`📊 ${categoryKey}.${item.id}.${permKey}: current=${currentValue}, initial=${initialValue}`)
          
          // Permission was added (assign)
          if (currentValue === true && initialValue === false) {
            console.log(`✅ ASSIGN: ${categoryKey}.${permKey} for item ${item.id}`)
            if (!assign[categoryKey]) assign[categoryKey] = {}
            if (!assign[categoryKey][permKey]) assign[categoryKey][permKey] = []
            assign[categoryKey][permKey].push(item.id)
          }
          
          // Permission was removed (revoke)
          if (currentValue === false && initialValue === true) {
            console.log(`❌ REVOKE: ${categoryKey}.${permKey} for item ${item.id}`)
            if (!revoke[categoryKey]) revoke[categoryKey] = {}
            if (!revoke[categoryKey][permKey]) revoke[categoryKey][permKey] = []
            revoke[categoryKey][permKey].push(item.id)
          }
        }
      }
    }
    
    const payload = {
      permissions: {
        assign: assign,
        revoke: revoke
      }
    }

    console.log('📤 Saving permissions:', JSON.stringify(payload, null, 2))
    
    const response = await API.patch(API.BULK_ASSIGN_PERMISSIONS(props.role.id), payload)
    
    if (!response.error) {
      console.log('✅ Permissions saved successfully')
      emit('permissionsUpdated')
      closeModal()
    }
  } catch (error) {
    console.error('❌ Error saving permissions:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  console.log('🔑 Role permissions manager mounted for role:', props.role.name)
  await fetchPermissions()
  loaded.value = true
})
</script>

<style scoped>
.permissions-manager-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 1.5rem;
}

.divider {
  margin: 0;
  border: none;
  border-top: 1px solid var(--ion-color-light-shade);
}

.title-with-role {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.title-with-role ion-icon {
  font-size: 1.5rem;
}

/* Role Info Header */
.role-info-header {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, var(--ion-color-light-tint) 0%, transparent 100%);
  border-radius: 12px;
  border: 1px solid var(--ion-color-light-shade);
}

.role-badge {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.role-color-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 3px solid var(--ion-color-light);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.role-details h2 {
  margin: 0 0 0.25rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--ion-color-dark);
}

.role-details p {
  margin: 0;
  font-size: 0.95rem;
  color: var(--ion-color-medium);
}

/* Permissions Section */
.permissions-section {
  margin-bottom: 2rem;
}

.permissions-loading,
.permissions-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  gap: 1rem;
  background: var(--ion-color-light-tint);
  border-radius: 12px;
}

.permissions-loading ion-spinner {
  width: 32px;
  height: 32px;
}

.permissions-loading p,
.permissions-empty p {
  margin: 0;
  color: var(--ion-color-medium);
  font-size: 0.95rem;
}

.empty-icon {
  font-size: 48px;
  color: var(--ion-color-medium);
  opacity: 0.5;
}

.permissions-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.permission-category-section {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--ion-color-light-shade);
}

.category-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--ion-color-light);
  border-bottom: 1px solid var(--ion-color-light-shade);
}

.category-icon {
  font-size: 20px;
  color: var(--ion-color-primary);
}

.category-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--ion-color-dark);
  flex: 1;
}

.item-count {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
  background: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-weight: 600;
}

.permission-items {
  display: flex;
  flex-direction: column;
}

.permission-item-card {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--ion-color-light);
}

.permission-item-card:last-child {
  border-bottom: none;
}

.item-name {
  margin-bottom: 0.75rem;
}

.item-name strong {
  font-size: 0.95rem;
  color: var(--ion-color-dark);
  display: block;
}

.item-permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.permission-checkbox {
  flex: 0 0 auto;
  min-width: 120px;
}

.permission-checkbox span {
  font-size: 0.85rem;
  color: var(--ion-color-dark);
}

.permission-checkbox .disabled-label {
  color: var(--ion-color-medium);
  text-decoration: line-through;
  opacity: 0.5;
}

/* Form Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--ion-color-light-shade);
}

/* Responsive */
@media (max-width: 768px) {
  .permissions-manager-container {
    padding: 1rem;
  }

  .form-actions {
    flex-direction: column;
  }

  .form-actions ion-button {
    width: 100%;
  }

  .item-permissions {
    flex-direction: column;
    gap: 0.5rem;
  }

  .permission-checkbox {
    min-width: auto;
  }

  .category-header {
    padding: 0.75rem 1rem;
  }

  .permission-item-card {
    padding: 0.75rem 1rem;
  }

  .role-badge {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
