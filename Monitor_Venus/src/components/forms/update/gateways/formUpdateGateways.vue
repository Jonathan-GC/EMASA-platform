<template>
  <ion-page>
    <ion-content class="ion-padding">
      <form-update
        v-if="loaded"
        :type="type"
        :index="index"
        :fields="formFields"
        :label="label"
        :additionalData="additionalData"
        :initialData="initialData"
        @itemEdited="handleitemEdited"
        @closed="emit('closed')"
      />
      <div v-else class="loading-container">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando formulario...</p>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonSpinner,
} from '@ionic/vue';
import API from '@utils/api/api';
// Assuming the previous component is named this.

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
});

const emit = defineEmits(['itemEdited', 'loaded']);

const loaded = ref(false);
const additionalData = ref({});
const formFields = ref([...props.fields]); // Use a ref to make a copy of the fields prop

// Method to handle item creation success
const handleitemEdited = () => {
  emit('itemEdited');
};

// Method to fetch user types from the API
const fetchWorkspaces = async () => {
  try {
    const workspaceValues = await API.get(API.WORKSPACE);
    const workspaceField = formFields.value.find(f => f.key === 'workspace_id');
    if (workspaceField) {
      workspaceField.options = workspaceValues.map((workspace: string) => ({
        label: workspace.name,
        value: workspace.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching sex values:', error);
  }
};

const fetchLocations = async () => {
  try {
    const locationValues = await API.get(API.LOCATION);
    const locationField = formFields.value.find(f => f.key === 'location_id');
    if (locationField) {
      locationField.options = locationValues.map((location: string) => ({
        label: location.name,
        value: location.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching sex values:', error);
  }
};
// Method to set additional data for the form
const setAffiliation = () => {
  additionalData.value = {
    ...additionalData.value,
    is_external_user: true
  };
  console.log("Additional Data Set:", additionalData.value);
};

// Run the data fetching and setup logic when the component is mounted
onMounted(async () => {
  // Avisa de inmediato al contenedor del modal (quickControl/quickActions)
  // que el formulario ya está montado; el spinner del modal no debe esperar
  // a los datos de referencia. El gate interno ("Cargando formulario...")
  // es el único spinner visible mientras se cargan las opciones.
  emit('loaded');
  //await fetchSex();
  //setAffiliation();
  // Carga en paralelo (antes eran dos await secuenciales = el doble de espera).
  await Promise.all([
    fetchWorkspaces(),
    fetchLocations(),
  ]);
  loaded.value = true;
});

/*const setInitialData = computed(() => {
  return {
    name: props.initialData.name,
  };
});*/
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
  font-size: 0.9rem;
}
</style>