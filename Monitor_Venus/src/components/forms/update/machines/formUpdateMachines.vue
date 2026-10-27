<template>
  <ion-page>
    <ion-content class="ion-padding">
      <FormUpdate
        v-if="loaded"
        :type="type"
        :index="index"
        :fields="formFields"
        :label="label"
        :additionalData="additionalData"
        :initialData="initialData"
        @itemEdited="handleItemEdited "
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
import { ref, onMounted } from 'vue';
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
  index: {
    type: Number,
  },
  label: {
    type: String,
    required: true,
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

const emit = defineEmits(['itemCreated', 'loaded', 'closed']);

const loaded = ref(false);
const additionalData = ref({});
const formFields = ref([...props.fields]); // Use a ref to make a copy of the fields prop

// Method to handle item creation success
const handleItemEdited = () => {
  emit('itemEdited');
};

// Method to fetch user types from the API
const fetchWorkspaces = async () => {
  try {
    const workspaces = await API.get(API.WORKSPACE);
    const workspaceField = formFields.value.find(f => f.key === 'workspace_id');
    if (workspaceField) {
      workspaceField.options = workspaces.map((workspace: string) => ({
        label: workspace.name,
        value: workspace.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching workspaces:', error);
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
  //await fetchTypes();
  //await fetchSex();
  //setAffiliation();
  await fetchWorkspaces();
  loaded.value = true;
});
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