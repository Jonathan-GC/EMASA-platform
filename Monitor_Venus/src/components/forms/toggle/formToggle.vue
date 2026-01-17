<template>
  <ion-content class="ion-padding">
    <ion-card-header class="custom">
      <ion-toolbar>
        <ion-title>{{ props.status ? 'Activar' : 'Desactivar' }} {{ label }}</ion-title>
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
            <ion-label>Esta a punto {{ props.status ? 'activar' : 'desactivar' }} el {{ label }} denominado {{ props.name }}, si esta seguro de que desea
              {{ props.status ? 'activar' : 'desactivar' }} este elemento por favor ingrese <span class="px-1"
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
  alt_name: {
    type: String,
    required: false,
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
  },
  status: {
    type: Boolean,
    required: false,
  }
});

console.log("index:", props.index);

const emit = defineEmits(['itemToggled', 'loaded', 'closed']);

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
  return props.alt_name ? `${props.status ? 'activar' : 'desactivar'} ${props.alt_name}` : `${props.status ? 'activar' : 'desactivar'} ${props.name}`;
});

const closeModal = () => {
  emit('closed');
}

async function deleteItem() {  // Renamed function
  loading.value = true;
  if (inputValue.value !== expectedValue.value) {
    alert(`Por favor ingrese "${expectedValue.value}" para confirmar.`);
    loading.value = false;
    return;
  }
  try {
    let response;
    // Map of types to API endpoints
    const apiEndpoints: Record<string, string> = {
      'user': props.status ? API.ACTIVATE_USER(props.index!) : API.DEACTIVATE_USER(props.index!),
    };
    const endpoint = apiEndpoints[props.type as string];
    if (endpoint) {
      response = await API.patch(endpoint);
      if (!response.error) {
        emit('itemToggled', props.index);
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