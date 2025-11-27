<template>
  <ion-page>

    <ion-content class="ion-padding">

      <ion-card-header class="custom">
        <ion-toolbar>
          <ion-title>Agregar {{ label }}</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeModal">
              <ion-icon :icon="icons.close" slot="icon-only"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-card-header>
      <hr class="divider" />
      <ion-card-content>
        <form @submit.prevent="createItem">
          <ion-list>
            <div v-for="(field, index) in fields" :key="index">
              <ion-item v-if="field.type === 'text'" class="custom">
                <ion-label class="!mb-2" position="stacked">{{ field.label }}</ion-label>
                <ion-input v-model="formValues[field.key]" class="custom" fill="solid" label-placement="floating" />
              </ion-item>

              <ion-item v-else-if="field.type === 'date'">
                <ion-input v-model="formValues[field.key]" :label="field.label" label-placement="floating"
                  type="date" />
              </ion-item>

              <ion-item v-else-if="field.type === 'radio-group'">
                <ion-radio-group v-model="formValues[field.key]">
                  <ion-list-header>
                    <ion-label>{{ field.label }}</ion-label>
                  </ion-list-header>
                  <ion-item v-for="(option, idx) in field.options" :key="idx">
                    <ion-radio :value="option.value">{{ option.label }}</ion-radio>
                  </ion-item>
                </ion-radio-group>
              </ion-item>

              <ion-item v-else-if="field.type === 'select'" class="custom">
                <ion-label position="stacked" class="!mb-2">{{ field.label }}</ion-label>
                <ModalSelector
                  v-model="formValues[field.key]"
                  :options="field.options || []"
                  :title="field.label || 'Seleccionar'"
                  :placeholder="field.placeholder || 'Seleccionar...'"
                  :disabled="field.disabled || false"
                  :searchable="field.searchable !== false"
                  display-field="label"
                  value-field="value"
                  @update:modelValue="handleFieldChange(field.key, $event)"
                >
                <template #display="{ selected }">
                    <span v-if="selected">{{ selected.label }}</span>
                    <span v-else class="text-gray-500">{{ field.placeholder || 'Seleccionar...' }}</span>
                  </template>
                  
                </ModalSelector>
              </ion-item>

              <ion-item v-else-if="field.type === 'multiple-select'">
                <ion-select multiple="true" v-model="formValues[field.key]" :label="field.label"
                  label-placement="floating">
                  <ion-select-option v-for="option in field.options" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </ion-select-option>
                </ion-select>
              </ion-item>

              <ion-item v-else-if="field.type === 'textarea'" class="custom">
                <ion-label position="stacked" class="!mb-2">{{field.label}}</ion-label>
                <ion-textarea v-model="formValues[field.key]" class="custom" fill="solid" rows="5"
                  ></ion-textarea>
              </ion-item>

              <ion-item v-else-if="field.type === 'checkbox'">
                <ion-checkbox v-model="formValues[field.key]" :checked="formValues[field.key]">
                  <ion-label>{{ field.label }}</ion-label>
                </ion-checkbox>
              </ion-item>

              <div v-else-if="field.type === 'image'" class="image-field-wrapper">
                <ImageUpload
                  :ref="el => setImageUploadRef(field.key, el)"
                  v-model="formValues[field.key]"
                  :placeholder-text="field.placeholder || 'Haz clic para seleccionar una imagen'"
                  :max-size="field.maxSize || 5 * 1024 * 1024"
                  :alt="field.label"
                  @change="handleImageChange(field.key, $event)"
                  @error="handleImageError"
                />
              </div>

            </div>
          </ion-list>
          <div class="ion-text-end ion-padding-top">
            <ion-button type="submit" :disabled="loading">
              <ion-spinner v-if="loading" slot="start"></ion-spinner>
              Guardar
            </ion-button>
          </div>
        </form>
      </ion-card-content>

    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, watch, toRefs, inject } from 'vue';
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonCard,
  IonCardContent,
  IonList,
  IonItem,
  IonLabel,
  IonInput,
  IonTextarea,
  IonSelect,
  IonSelectOption,
  IonRadioGroup,
  IonRadio,
  IonListHeader,
  IonCheckbox,
  IonButton,
  IonSpinner,
} from '@ionic/vue';
import ModalSelector from '@/components/ui/ModalSelector.vue';
import ImageUpload from '@/components/common/ImageUpload.vue';
import API from "@utils/api/api";

const props = defineProps({
  type: String,
  label: String,
  fields: {
    type: Object,
    default: () => ({}),
  },
  additionalData: {
    type: Object,
    default: () => ({}),
  }
});

const emit = defineEmits(['itemCreated', 'fieldChanged', 'closed']);

const { fields, additionalData } = toRefs(props);

const loading = ref(false);
const formValues = ref({ ...fields.value, ...fields.value, ...additionalData.value });
const componentKey = ref(0);
const imageUploadRefs = ref({});

const icons = inject('icons', {});

// Store refs for ImageUpload components
const setImageUploadRef = (key, el) => {
  if (el) {
    imageUploadRefs.value[key] = el;
  }
};

const closeModal = () => {
  emit('closed');
}

// Watch for changes in props.fields to update formValues
watch(fields, (newFields) => {
  formValues.value = { ...newFields, ...additionalData.value };
}, { deep: true });

function handleFieldChange(fieldKey, value) {
  formValues.value[fieldKey] = value;
  if (value === null || value === '') {
    componentKey.value++;
  }
  emit('fieldChanged', fieldKey, value);
}

function handleImageChange(fieldKey, fileInfo) {
  console.log(`📸 Image changed for ${fieldKey}:`, fileInfo);
  // Store the file info for later use
  formValues.value[`${fieldKey}_file`] = fileInfo.file;
}

function handleImageError(errorMessage) {
  console.error('❌ Image upload error:', errorMessage);
}

function clearField(fieldKey) {
  formValues.value[fieldKey] = null;
  componentKey.value++;
}

async function createItem() {
  loading.value = true;
  try {
    let response;
    
    // Get deviceId from additionalData if type is measurements
    const deviceId = props.additionalData?.device_id;
    
    // Map of types to API endpoints
    const apiEndpoints = {
      'tenant': API.TENANT,
      'gateway': API.GATEWAY,
      'location': API.LOCATION,
      'device_profile': API.DEVICE_PROFILE,
      'device': API.DEVICE,
      'device_activation': API.DEVICE,
      'machine': API.MACHINE,
      'application': API.APPLICATION,
      'workspace': API.WORKSPACE,
      'manager': API.API_USER,
      'user': API.USERS,
      'role': API.ROLES,
      'measurement': deviceId ? API.DEVICE_CREATE_MEASUREMENTS(deviceId) : null,

    };
    const endpoint = apiEndpoints[props.type];
    if (endpoint) {
      // Check if any image fields have files
      const hasImageFiles = Object.keys(imageUploadRefs.value).some(key => {
        const fileInfo = imageUploadRefs.value[key]?.getFileInfo();
        return fileInfo?.file;
      });

      let payload;
      if (hasImageFiles) {
        // Use FormData if there are image files
        console.log('📦 Using FormData for file upload');
        const formData = new FormData();
        
        // Add all form values
        Object.keys(formValues.value).forEach(key => {
          if (!key.endsWith('_file') && formValues.value[key] !== null && formValues.value[key] !== undefined) {
            // Convert dev_eui to lowercase
            const value = key === 'dev_eui' && typeof formValues.value[key] === 'string' 
              ? formValues.value[key].toLowerCase() 
              : formValues.value[key];
            formData.append(key, value);
          }
        });
        
        // Add image files
        Object.keys(imageUploadRefs.value).forEach(key => {
          const fileInfo = imageUploadRefs.value[key]?.getFileInfo();
          if (fileInfo?.file) {
            formData.append(key, fileInfo.file);
          }
        });
        
        payload = formData;
      } else {
        // Use JSON if no files
        console.log('📄 Using JSON payload (no files)');
        payload = { ...formValues.value } as any;
        // Convert dev_eui to lowercase
        if (payload.dev_eui && typeof payload.dev_eui === 'string') {
          payload.dev_eui = payload.dev_eui.toLowerCase();
        }
        // Remove file references
        Object.keys(payload).forEach(key => {
          if (key.endsWith('_file')) {
            delete payload[key];
          }
        });
      }

      response = await API.post(endpoint, payload);
      if (!response.error) {
        emit('itemCreated', formValues.value.name);
      }
    } else {
      console.error("Unknown type:", props.type);
    }
  } catch (error) {
    console.error("Error al crear", error);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* Wrapper para el campo de selección */
.select-field-wrapper {
  margin-bottom: 1rem;
  padding: 0 16px;
}

.select-field-wrapper ion-label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 14px;
  color: var(--ion-color-step-600);
}

/* Asegurar que el ModalSelector tenga el mismo estilo que otros inputs */
.select-field-wrapper :deep(.modal-selector-button) {
  width: 100%;
  min-height: 48px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.select-field-wrapper :deep(.modal-selector-button:hover:not(.disabled)) {
  background-color: var(--ion-color-light-shade);
}

.select-field-wrapper :deep(.modal-selector-button.disabled) {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Image field wrapper */
.image-field-wrapper {
  margin-bottom: 1.5rem;
  padding: 16px;
}

.image-field-wrapper .field-label {
  display: block;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: var(--ion-color-step-600);
}
</style>