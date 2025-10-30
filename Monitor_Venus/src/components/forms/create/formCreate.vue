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
                <ion-item v-if="field.type === 'text'">
                  <ion-input v-model="formValues[field.key]" :label="field.label" label-placement="floating" />
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

                <ion-item v-else-if="field.type === 'select'">
                  <ion-select :key="`${field.key}-${componentKey}`" v-model="formValues[field.key]" :label="field.label"
                    label-placement="floating" :disabled="field.disabled" :required="field.required"
                    @ion-change="handleFieldChange(field.key, $event.detail.value)">
                    <ion-select-option v-for="option in field.options" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </ion-select-option>
                  </ion-select>
                </ion-item>

                <ion-item v-else-if="field.type === 'multiple-select'">
                  <ion-select multiple="true" v-model="formValues[field.key]" :label="field.label"
                    label-placement="floating">
                    <ion-select-option v-for="option in field.options" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </ion-select-option>
                  </ion-select>
                </ion-item>

                <ion-item v-else-if="field.type === 'textarea'">
                  <ion-textarea v-model="formValues[field.key]" :label="field.label" label-placement="floating"
                    rows="5" />
                </ion-item>

                <ion-item v-else-if="field.type === 'checkbox'">
                  <ion-checkbox v-model="formValues[field.key]" :checked="formValues[field.key]">
                    <ion-label>{{ field.label }}</ion-label>
                  </ion-checkbox>
                </ion-item>
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
const formValues = ref({ ...fields.value, ...additionalData.value });
const componentKey = ref(0);

const icons = inject('icons', {});

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

function clearField(fieldKey) {
  formValues.value[fieldKey] = null;
  componentKey.value++;
}

async function createItem() {
  loading.value = true;
  try {
    let response;
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
    };
    const endpoint = apiEndpoints[props.type];
    if (endpoint) {
      response = await API.post(endpoint, { ...formValues.value });
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