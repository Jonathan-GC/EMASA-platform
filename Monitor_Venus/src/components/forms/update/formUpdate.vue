<template>
  <ion-page>

    <ion-content class="ion-padding">
      <ion-card-header class="custom">
        <ion-toolbar>
          <ion-title>Actualizar {{ label }}</ion-title>
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
            <div v-for="(field, index) in filteredFields" :key="index">
              <ion-item v-if="field.type === 'text'" class="custom">
                <ion-label class="!mb-2" position="stacked">{{ field.label }}</ion-label>
                <ion-input v-model="formValues[field.key]" class="custom" fill="solid" />
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

              <ion-item v-else-if="field.type === 'icon'" class="custom">
                <ion-label position="stacked" class="!mb-2">{{ field.label }}</ion-label>
                <IconPicker
                  v-model="formValues[field.key]"
                  :title="field.label || 'Seleccionar Icono'"
                  :placeholder="field.placeholder || 'Seleccionar icono...'"
                  :disabled="field.disabled || false"
                  :searchable="field.searchable !== false"
                  @update:modelValue="handleFieldChange(field.key, $event)"
                />
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

              <ion-item v-else-if="field.type === 'map'" class="custom no-lines">
                <div class="map-field-full-width">
                  <ion-label class="!mb-2">{{ field.label }}</ion-label>
                  <InlineMap 
                    v-model:lat="formValues.latitude"
                    v-model:lng="formValues.longitude"
                    @change="onInlineMapChange"
                  />
                </div>
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

    <MapPicker
      :show="mapModalOpen"
      :initial="mapInitial"
      :title="label"
      @update:show="mapModalOpen = $event"
      @selected="onMapSelected"
    />
  </ion-page>
</template>

<script setup lang="ts">
import { ref, watch, toRefs, inject, computed } from 'vue';
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
import IconPicker from '@/components/ui/IconPicker.vue';
import ImageUpload from '@/components/common/ImageUpload.vue';
import MapPicker from '@/components/maps/MapPicker.vue';
import InlineMap from '@/components/maps/InlineMap.vue';
import API from "@utils/api/api";
import { useResponsiveView } from '@/composables/useResponsiveView';

const props = defineProps({
  type: String,
  index: {
    type: Number,
  },
  label: String,
  fields: {
    type: Object,
    default: () => ({}),
  },
  additionalData: {
    type: Object,
    default: () => ({}),
  },
  initialData: {
    type: Object,
    default: () => ({}),
  },
  reqIndex: {
    type: Boolean,
    default: true,
  },
});

console.log("index:", props.index);

const emit = defineEmits(['itemEdited', 'fieldChanged', 'closed']);

const { fields, additionalData } = toRefs(props);
const { isMobile } = useResponsiveView();

const loading = ref(false);

const filteredFields = computed(() => {
  if (!Array.isArray(props.fields)) return [];
  return props.fields.filter(field => field.key !== 'accuracy' && field.key !== 'source');
});

// Properly initialize formValues from fields array and initialData
const initializeFormValues = (fieldsArray) => {
  const values = {};
  if (Array.isArray(fieldsArray)) {
    fieldsArray.forEach(field => {
      values[field.key] = field.value !== undefined ? field.value : null;
    });
  }
  // Order of priority: field default values < additionalData < initialData
  return { ...values, ...additionalData.value, ...props.initialData };
};

const formValues = ref(initializeFormValues(props.fields));
const componentKey = ref(0);
const imageUploadRefs = ref({});

const icons = inject('icons',{});

// Map picker state
const mapModalOpen = ref(false);
const mapInitial = ref(null);
let currentMapFieldKey = '';

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
// Preserve initialData when fields update (e.g., after fetching dropdown options)
watch(fields, (newFields) => {
  formValues.value = initializeFormValues(newFields);
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

// Map Picker functions
function openMap(fieldKey) {
  currentMapFieldKey = fieldKey;
  // Try to find current coordinates
  const latValue = formValues.value.latitude;
  const lngValue = formValues.value.longitude;

  if (latValue && lngValue) {
    mapInitial.value = { lat: parseFloat(latValue), lng: parseFloat(lngValue) };
  } else {
    mapInitial.value = null;
  }
  
  mapModalOpen.value = true;
}

function onMapSelected(coord) {
  console.log('📍 Map coordinates selected:', coord);
  
  // Set the specific field if it exists
  if (currentMapFieldKey) {
    formValues.value[currentMapFieldKey] = `${coord.lat.toFixed(6)}, ${coord.lng.toFixed(6)}`;
  }
  
  // Also try to automatically fill latitude and longitude fields if they exist in schema
  const hasLatField = props.fields.some(f => f.key === 'latitude');
  const hasLngField = props.fields.some(f => f.key === 'longitude');
  
  if (hasLatField) formValues.value.latitude = coord.lat.toFixed(6);
  if (hasLngField) formValues.value.longitude = coord.lng.toFixed(6);
  
  emit('fieldChanged', 'latitude', coord.lat.toFixed(6));
  emit('fieldChanged', 'longitude', coord.lng.toFixed(6));
}

function onInlineMapChange(coord) {
  console.log('📍 Inline map coordinates changed:', coord);
  formValues.value.latitude = coord.lat;
  formValues.value.longitude = coord.lng;
  
  emit('fieldChanged', 'latitude', coord.lat);
  emit('fieldChanged', 'longitude', coord.lng);
}

async function createItem() {
  loading.value = true;
  try {
    let response;

    // Inject accuracy and source for locations
    if (props.type === 'location') {
      formValues.value.accuracy = isMobile.value ? 10 : 25;
      formValues.value.source = 'GPS';
    }

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
      'group': API.INVESTIGATION_GROUPS,
      'seedbed': API.RESEARCH_SEEDBEDS,
      'user_integra': API.USERS_INTEGRA,
      'user_external': API.USERS,
      'role': API.ROLES,
      'functionary_profile': API.FUNCTIONARY_PROFILES,
      'student_profile': API.STUDENT_PROFILES,
      'external_profile': API.EXTERNAL_USER_PROFILES,
      'external_seedbed_profile': API.EXTERNAL_USER_PROFILES,
      'group_profile': API.INVESTIGATION_GRUOPS_PROFILES,
      'seedbed_profile': API.RESEARCH_SEEDBEDS_PROFILES,
      'seedbed_member': API.RESEARCH_SEEDBEDS_MEMBERS,
      'measurement': API.DEVICE_UPDATE_MEASUREMENTS,
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

      if (!props.reqIndex) {
        response = await API.patch(`${endpoint}`, payload);
      } else {
        response = await API.patch(`${endpoint}${props.index}/`, payload);
      }
      if (!response.error) {
          emit('itemEdited', formValues.value.name);
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

/* Map field styles */
.map-field-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 0;
}

.map-values {
  display: flex;
  flex-direction: column;
}

.map-val {
  display: flex;
  flex-direction: column;
  font-size: 14px;
  color: var(--ion-color-step-800);
  font-family: monospace;
}

.map-placeholder {
  font-style: italic;
  color: var(--ion-color-step-400);
  font-size: 14px;
}

.map-btn {
  --padding-start: 0;
  --padding-end: 0;
  font-weight: 600;
  text-transform: none;
}

.map-field-full-width {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.no-lines {
  --inner-padding-end: 0;
  --padding-start: 16px;
}
</style>