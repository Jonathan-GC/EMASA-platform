<template>
    <ion-card-header>
      <div class="flex">
      <h3 class="flex-1">Device Activation Management</h3>
      <ion-item lines="none" class="toggle-item flex-1">
          <ion-toggle
            v-model="activationToggle"
            :disabled="activationLoading"
            @ion-change="handleActivationToggle"
            slot="end"
            :color="isActivated ? 'success' : 'medium'"
          />
        </ion-item>
        </div>
      <ion-card-subtitle class="section-description !mb-1">Set up LoRaWAN communications. Enter the activation keys in order to activate this device on the network.</ion-card-subtitle>
    </ion-card-header>
    <ion-card-content>

      <!-- Section 1: Device Activation Control -->
      <!--<div v-if="activeDeviceId" class="activation-control-section">
        <h3>Device Activation Control</h3>
        <ion-item lines="none" class="status-item">
          <ion-label>
            <h4>Current Status</h4>
            <p>{{ deviceStatusMessage }}</p>
          </ion-label>
          <ion-badge
            slot="end"
            :color="isActivated ? 'success' : 'medium'"
          >
            {{ isActivated ? '✓ Active' : '○ Inactive' }}
          </ion-badge>
        </ion-item>

        
        <ion-progress-bar
          v-if="activationLoading"
          type="indeterminate"
          color="primary"
        ></ion-progress-bar>
      </div>-->

      <hr v-if="activeDeviceId" class="section-divider" />

      <!-- Section 2: Activation Keys Configuration -->
      <div class="keys-configuration-section">
                <!-- Loading indicator for activation details -->
        <div v-if="loadingActivationDetails" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Loading activation details...</p>
        </div>

        <form @submit.prevent="submitActivationKeys">
          <ion-list>
            <!-- Device Address -->
            <ion-item class="custom">
              <ion-label position="stacked" class="!mb-2">Device Address</ion-label>
              <ion-input
                fill="solid"
                v-model="formData.dev_addr"
                placeholder="Enter device address"
                required
                :counter="true"
                maxlength="8"
                class="custom"
              />
            </ion-item>

            <!-- Application Session Key -->
            <ion-item class="custom">
              <ion-label position="stacked" class="!mb-2">Application Session Key</ion-label>
              <ion-input
                fill="solid"
                v-model="formData.app_s_key"
                placeholder="Enter application session key"
                required
                :counter="true"
                maxlength="32"
                class="custom"
              />
            </ion-item>

            <!-- Network Session Key -->
            <ion-item class="custom">
              <ion-label position="stacked" class="!mb-2">Network Session Key (NwkSEncKey)</ion-label>
              <ion-input
                fill="solid"
                v-model="formData.nwk_s_enc_key"
                placeholder="Enter network session key"
                :counter="true"
                maxlength="32"
                class="custom"
              />
            </ion-item>

            <!-- Frame Counters Section -->
            <div class="frame-counters-section">
              <h4>Frame Counters (Optional)</h4>
              
              <!-- Uplink Frame Counter -->
              <div class="flex">
              <ion-item class="custom flex-1 !mr-2">
                <ion-label position="stacked" class="!mb-2">Uplink Frame Counter</ion-label>
                <ion-input
                  fill="solid"
                  v-model="formData.f_cnt_up"
                  placeholder="0"
                  type="number"
                  min="0" 
                  class="custom"
                />
              </ion-item>

              <!-- Network Downlink Counter -->
              <ion-item class="custom flex-1 !mr-2">
                <ion-label position="stacked" class="!mb-2">Network Downlink Counter</ion-label>
                <ion-input
                  fill="solid"
                  v-model="formData.n_f_cnt_down"
                  placeholder="0"
                  type="number"
                  min="0"
                  class="custom"
                />
              </ion-item>

              <!-- Application Downlink Counter -->
              <ion-item class="custom flex-1">
                <ion-label position="stacked" class="!mb-2">Application Downlink Counter</ion-label>
                <ion-input
                  fill="solid"
                  v-model="formData.afcntdown"
                  placeholder="0"
                  type="number"
                  min="0"
                  class="custom"
                />
              </ion-item>
              </div>
            </div>
          </ion-list>

          <div class="button-group ion-padding-top">
            <ion-button
              type="submit"
              :disabled="keysLoading || !isKeysFormValid"
              class="set-keys-button"
            >
              <ion-spinner v-if="keysLoading" slot="start"></ion-spinner>
              <ion-icon v-else :icon="icons.key" slot="start"></ion-icon>
              Set Activation Keys
            </ion-button>
          </div>
        </form>
      </div>

    </ion-card-content>
  
</template>

<script setup>
import { ref, computed, defineProps, defineEmits, watch, inject, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import {
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonList,
  IonItem,
  IonInput,
  IonButton,
  IonSpinner,
  IonBadge,
  IonToggle,
  IonLabel,
  IonProgressBar,
  IonIcon,
} from '@ionic/vue'
import API from '@utils/api/api'

// Get device ID from URL
const route = useRoute()
const deviceIdFromRoute = computed(() => route.params.device_id)

// Inject icons
const icons = inject('icons', {})

// Props
const props = defineProps({
  type: String,
  label: String,
  fields: {
    type: Array,
    default: () => [],
  },
  device: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['itemCreated', 'fieldChanged', 'activationChanged', 'closed'])

// State management
const keysLoading = ref(false)
const activationLoading = ref(false)
const isActivated = ref(false)
const loadingActivationDetails = ref(false)

const formData = ref({
  dev_addr: '',
  app_s_key: '',
  f_nwk_s_int_key: '',
  s_nwk_s_int_key: '',
  nwk_s_enc_key: '',
  f_cnt_up: '',
  n_f_cnt_down: '',
  afcntdown: ''
})

// Computed property to get the active device ID (from route or props)
const activeDeviceId = computed(() => {
  return deviceIdFromRoute.value || props.device?.id
})

// Computed properties
const activationToggle = computed({
  get: () => isActivated.value,
  set: (value) => {
    // Handled by ion-change event
  }
})

const deviceStatusMessage = computed(() => {
  if (!activeDeviceId) return 'No device selected'
  if (!props.device) return 'Device information loading...'
  if (isActivated.value) {
    return 'Device is activated and ready to communicate'
  }
  return 'Device is inactive - configure keys and activate'
})

const isKeysFormValid = computed(() => {
  // Only require the fields that are actually in the form
  return formData.value.dev_addr.trim() &&
         formData.value.app_s_key.trim() &&
         formData.value.nwk_s_enc_key.trim()
  // nwk_s_enc_key is optional
  // Counters are optional
})

// Watch for device changes
watch(() => props.device, (newDevice, oldDevice) => {
  console.log('👀 Device watcher triggered')
  console.log('📦 New device:', newDevice)
  console.log('📦 Old device:', oldDevice)
  console.log('🆔 Device ID:', newDevice?.id)
  
  if (newDevice) {
    // Update activation status from device data
    isActivated.value = newDevice.is_activated || false
    console.log('🔄 Activation status set to:', isActivated.value)
  }
  
  // Always try to fetch activation details if we have a device ID
  if (activeDeviceId.value) {
    fetchActivationDetails()
  }
}, { immediate: true })

// Fetch activation details from API
async function fetchActivationDetails() {
  if (!activeDeviceId.value) {
    console.warn('⚠️ No device ID available for fetching activation details')
    return
  }

  loadingActivationDetails.value = true
  try {
    console.log('📡 Fetching activation details for device:', activeDeviceId.value)
    
    const response = await API.get(API.DEVICE_ACTIVATION_DETAILS(activeDeviceId.value))
    
    // Check if response indicates no activation data
    if (response.message === 'Device has no activation data') {
      console.log('ℹ️ Device has no activation data - form will remain empty')
      return
    }
    
    // Handle error responses
    if (response.error) {
      console.warn('⚠️ Error fetching activation details:', response.error)
      return
    }
    
    // Populate form with activation data
    if (response) {
      console.log('✅ Activation details loaded:', response)
      console.log('📋 Response type:', typeof response)
      console.log('📋 Response keys:', Object.keys(response))
      console.log('📋 Response dev_addr:', response.dev_addr)
      console.log('📋 Response app_s_key:', response.app_s_key)
      
      // Handle different response formats
      let activationData = response
      
      // Check if response is wrapped in an array (like other API responses)
      if (Array.isArray(response) && response.length > 0) {
        console.log('📦 Response is an array, using first element')
        activationData = response[0]
      }
      
      // Set form data field by field for better reactivity
      formData.value.dev_addr = activationData.dev_addr || ''
      formData.value.app_s_key = activationData.app_s_key || ''
      formData.value.f_nwk_s_int_key = activationData.f_nwk_s_int_key || ''
      formData.value.s_nwk_s_int_key = activationData.s_nwk_s_int_key || ''
      formData.value.nwk_s_enc_key = activationData.nwk_s_enc_key || ''
      formData.value.f_cnt_up = activationData.f_cnt_up?.toString() || ''
      formData.value.n_f_cnt_down = activationData.n_f_cnt_down?.toString() || ''
      formData.value.afcntdown = activationData.afcntdown?.toString() || ''
      
      console.log('📝 Form data populated:', formData.value)
      console.log('📝 formData.dev_addr:', formData.value.dev_addr)
      console.log('📝 formData.app_s_key:', formData.value.app_s_key)
      
      // Update activation status if available
      if (activationData.is_activated !== undefined) {
        isActivated.value = activationData.is_activated
        console.log('🔄 Activation status updated:', isActivated.value)
      }
      
      // Force reactive update
      await nextTick()
      console.log('🔄 Reactive update completed')
    }
    
  } catch (error) {
    console.error('❌ Error fetching activation details:', error)
    // Don't show error to user - just log it and continue with empty form
  } finally {
    loadingActivationDetails.value = false
  }
}

// Initialize form with device data (legacy function - kept for compatibility)
function initializeForm() {
  if (props.device) {
    if (props.device.dev_addr) {
      formData.value.dev_addr = props.device.dev_addr
    }
    // Add other pre-fill logic as needed
  }
}

// Submit activation keys (Step 1)
async function submitActivationKeys() {
  if (!isKeysFormValid.value || !activeDeviceId.value) {
    console.warn('⚠️ Form validation failed or no device ID available')
    console.warn('Device ID from route:', deviceIdFromRoute.value)
    console.warn('Device ID from props:', props.device?.id)
    return
  }

  keysLoading.value = true
  try {
    console.log('🔑 Setting activation keys for device:', activeDeviceId.value)
    
    const keysPayload = {
      dev_addr: formData.value.dev_addr,
      app_s_key: formData.value.app_s_key,
      f_nwk_s_int_key: formData.value.nwk_s_enc_key || '',
      s_nwk_s_int_key: formData.value.nwk_s_enc_key || '',
      nwk_s_enc_key: formData.value.nwk_s_enc_key || '',
      f_cnt_up: parseInt(formData.value.f_cnt_up) || 0,
      n_f_cnt_down: parseInt(formData.value.n_f_cnt_down) || 0,
      afcntdown: parseInt(formData.value.afcntdown) || 0
    }

    const response = await API.post(
      API.DEVICE_SET_ACTIVATION_KEYS(activeDeviceId.value),
      keysPayload
    )

    if (!response.error && !response[0]?.error) {
      console.log('✅ Activation keys set successfully')
      emit('itemCreated', `Activation keys configured for ${props.device?.device_name || 'device'}`)
      // Optionally show success toast here
    } else {
      throw new Error(response.error || response[0]?.error || 'Failed to set keys')
    }
  } catch (error) {
    console.error('❌ Error setting activation keys:', error)
    emit('itemCreated', `Error: ${error.message}`)
    // Optionally show error toast here
  } finally {
    keysLoading.value = false
  }
}

// Handle activation toggle (Step 2)
async function handleActivationToggle(event) {
  const shouldActivate = event.detail.checked

  if (!activeDeviceId.value) {
    console.warn('⚠️ No device ID available')
    console.warn('Device ID from route:', deviceIdFromRoute.value)
    console.warn('Device ID from props:', props.device?.id)
    event.target.checked = isActivated.value
    return
  }

  activationLoading.value = true
  
  try {
    if (shouldActivate) {
      // Activate device
      console.log('🚀 Activating device:', activeDeviceId.value)
      
      const response = await API.post(
        API.DEVICE_ACTIVATION(activeDeviceId.value),
        {}
      )

      if (!response.error && !response[0]?.error) {
        isActivated.value = true
        console.log('✅ Device activated successfully')
        emit('itemCreated', `Device ${props.device?.device_name || 'Unknown'} activated`)
        emit('activationChanged', true)
      } else {
        throw new Error(response.error || response[0]?.error || 'Activation failed')
      }
    } else {
      // Deactivate device
      console.log('🛑 Deactivating device:', activeDeviceId.value)
      
      const response = await API.post(
        API.DEVICE_DEACTIVATION(activeDeviceId.value),
        {}
      )

      if (!response.error && !response[0]?.error) {
        isActivated.value = false
        console.log('✅ Device deactivated successfully')
        emit('itemCreated', `Device ${props.device?.device_name || 'Unknown'} deactivated`)
        emit('activationChanged', false)
      } else {
        throw new Error(response.error || response[0]?.error || 'Deactivation failed')
      }
    }
  } catch (error) {
    console.error(`❌ Error ${shouldActivate ? 'activating' : 'deactivating'} device:`, error)
    // Revert toggle on error
    event.target.checked = isActivated.value
    emit('itemCreated', `Error: ${error.message}`)
  } finally {
    activationLoading.value = false
  }
}

// Field change handler (for compatibility)
function handleFieldChanged(fieldKey, value) {
  emit('fieldChanged', fieldKey, value)
}

const closeModal = () => {
  emit('closed')
}

// Debug logging on mount
onMounted(() => {
  console.log('🔍 FormActivationDevice mounted')
  console.log('📍 Device ID from route:', deviceIdFromRoute.value)
  console.log('📦 Device from props:', props.device)
  console.log('✅ Active device ID:', activeDeviceId.value)
  
  // Fetch activation details if we have a device ID (from route or props)
  if (activeDeviceId.value) {
    console.log('📡 Fetching activation details on mount')
    fetchActivationDetails()
  } else {
    console.log('⚠️ No device ID available on mount')
  }
})
</script>

<style scoped>
/* Device activation form styles */
ion-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

ion-card-header {
  padding-bottom: 8px;
}

ion-card-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #374151;
}

ion-card-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
  margin-top: 4px;
  line-height: 1.4;
}

/* Section Headers */
.activation-control-section h3,
.keys-configuration-section h3 {
  margin: 0 0 16px 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  border-bottom: 2px solid #3b82f6;
  padding-bottom: 8px;
}

/* Activation Control Section */
.activation-control-section {
  margin-bottom: 24px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.status-item,
.toggle-item {
  --background: #ffffff;
  --border-radius: 8px;
  margin-bottom: 12px;
  box-shadow: none;
}

.status-item h4,
.toggle-item h4 {
  margin: 0 0 4px 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
}

.status-item p,
.toggle-item p {
  margin: 0;
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.3;
}

ion-badge {
  font-size: 0.75rem;
  padding: 6px 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}



ion-progress-bar {
  margin-top: 8px;
  height: 3px;
}

/* Keys Configuration Section */
.keys-configuration-section {
  margin-top: 20px;
}

.section-description {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0 0 20px 0;
  line-height: 1.5;
  padding: 12px;
  background: #f8fafc;
  border-left: 3px solid #3b82f6;
  border-radius: 4px;
}

/* Frame Counters Section */
.frame-counters-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.frame-counters-section h4 {
  margin: 0 0 16px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

/* Form Lists and Items */
ion-list {
  background: transparent;
  padding: 0;
}

ion-item {
  --border-radius: 8px;
  --padding-start: 0;
  --inner-padding-end: 0;
  --border-color: #e5e7eb;
  --background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

ion-input {
  --placeholder-color: #9ca3af;
  --color: #374151;
  font-size: 0.9rem;
}

/* Required field indicator */
ion-item ion-input[required] {
  --border-color: #f59e0b;
}

ion-item ion-input[required]:focus-within {
  --border-color: #3b82f6;
}

/* Helper text styling */
ion-input::part(helper-text) {
  color: #6b7280;
  font-size: 0.75rem;
  margin-top: 4px;
}

/* Button Group */
.button-group {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.set-keys-button {
  --background: #3b82f6;
  --background-hover: #2563eb;
  --background-activated: #1d4ed8;
  --color: #ffffff;
  --border-radius: 6px;
  --padding-start: 16px;
  --padding-end: 16px;
  --padding-top: 10px;
  --padding-bottom: 10px;
  font-weight: 500;
  font-size: 0.9rem;
  min-height: 40px;
  text-transform: none;
}

.set-keys-button:disabled {
  --background: #d1d5db;
  --color: #9ca3af;
}

/* Loading container for activation details */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 20px;
}

.loading-container ion-spinner {
  margin-bottom: 12px;
}

.loading-container p {
  margin: 0;
  font-size: 0.9rem;
  color: #64748b;
}

/* Divider */
.section-divider {
  border: none;
  border-top: 2px solid #e5e7eb;
  margin: 24px 0;
  height: 0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  ion-card-title {
    font-size: 1.1rem;
  }

  .activation-control-section h3,
  .keys-configuration-section h3 {
    font-size: 1rem;
  }

  ion-item {
    margin-bottom: 12px;
  }

  .set-keys-button {
    width: auto;
    --padding-start: 12px;
    --padding-end: 12px;
  }

  .status-item h4,
  .toggle-item h4 {
    font-size: 0.9rem;
  }

  .status-item p,
  .toggle-item p {
    font-size: 0.75rem;
  }
}

/* Animation for status changes */
.status-item ion-badge,
.toggle-item ion-toggle {
  transition: all 0.3s ease;
}

/* Focus styles for accessibility */
ion-button:focus,
ion-toggle:focus,
ion-input:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>