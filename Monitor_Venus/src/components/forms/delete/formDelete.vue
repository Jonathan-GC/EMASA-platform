<template>
  <ion-content class="ion-padding">
    <ion-card-header class="custom">
      <ion-toolbar>
        <ion-title>Eliminar {{ label }}</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeModal">
            <ion-icon :icon="icons.close" slot="icon-only"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-card-header>
    <hr class="divider" />
    <ion-card-content class="custom">
      <form @submit.prevent="deleteItem">  <!-- Renamed for clarity -->
        <ion-list>
          <ion-item class="custom">
            <ion-label>Esta a punto eliminar el {{ label }} denominado {{ props.name }}, si esta seguro de que desea
              eliminar este elemento por favor ingrese <span class="px-1"
                style="background-color:var(--color-zinc-200); color: var(--color-zinc-600)"> {{ expectedValue
                }}</span></ion-label>
          </ion-item>
          <ion-item class="custom">
            <ion-input class="custom" v-model="inputValue" :placeholder="expectedValue" fill="solid" />
          </ion-item>
        </ion-list>
        <div class="ion-text-end ion-padding-top">
          <ion-button type="submit" :disabled="loading || inputValue !== expectedValue">
            <ion-spinner v-if="loading" slot="start"></ion-spinner>
            Guardar
          </ion-button>
        </div>
      </form>
    </ion-card-content>
  </ion-content>
</template>

<script setup lang="ts">
import { ref, watch, toRefs, computed, inject, onMounted } from 'vue';
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
  name: {
    type: String,
  },
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
  }
});

console.log("index:", props.index);

const emit = defineEmits(['itemDeleted', 'loaded', 'closed']);

const { fields, additionalData } = toRefs(props);

const loading = ref(false);
const formValues = ref({ ...fields.value, ...additionalData.value, ...props.initialData });
const componentKey = ref(0);
const inputValue = ref('');  // New ref for input binding
const isOpen = ref(false)

const icons = inject('icons', {})
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

const expectedValue = computed(() => {
  return props.alt_name ? `eliminar ${props.alt_name}` : `eliminar ${props.name}`;
});

const closeModal = () => {
  emit('closed');
}

async function deleteItem() {  // Renamed function
  loading.value = true;
  if (inputValue.value !== expectedValue.value) {
    alert(`Por favor ingrese "${expectedValue.value}" para confirmar la eliminación.`);
    loading.value = false;
    return;
  }
  try {
    const deviceId = props.additionalData?.device_id;
    let response;
    // Map of types to API endpoints
    const apiEndpoints = {
      'tenant': API.TENANT,
      'gateway': API.GATEWAY,
      'location': API.LOCATION,
      'device_profile': API.DEVICE_PROFILE,
      'device': API.DEVICE,
      'device_activation': API.DEVICE,
      'device_type': API.DEVICE_TYPES,
      'machine': API.MACHINE,
      'application': API.APPLICATION,
      'workspace': API.WORKSPACE,
      'manager': API.API_USER,
      'group': API.INVESTIGATION_GROUPS,
      'seedbed': API.RESEARCH_SEEDBEDS,
      'user_integra': API.USERS_INTEGRA,
      'user_external': API.USERS,
      'role': API.ROLE,
      'functionary_profile': API.FUNCTIONARY_PROFILES,
      'student_profile': API.STUDENT_PROFILES,
      'external_profile': API.EXTERNAL_USER_PROFILES,
      'external_seedbed_profile': API.EXTERNAL_USER_PROFILES,
      'group_profile': API.INVESTIGATION_GRUOPS_PROFILES,
      'seedbed_profile': API.RESEARCH_SEEDBEDS_PROFILES,
      'seedbed_member': API.RESEARCH_SEEDBEDS_MEMBERS,
      'measurement': API.DEVICE_DELETE_MEASUREMENTS,
    };
    const endpoint = apiEndpoints[props.type];
    if (endpoint) {
      response = await API.delete(`${endpoint}${props.index}/`);
      if (!response.error) {
        emit('itemDeleted', formValues.value.name);  // Fixed emit event
      }
    } else {
      console.error("Unknown type:", props.type);
    }
  } catch (error) {
    console.error("Error al eliminar", error);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  emit('loaded');
});
</script>