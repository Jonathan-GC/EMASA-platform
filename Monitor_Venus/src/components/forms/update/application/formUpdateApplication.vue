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
const fetchTypes = async () => {
  try {
    const integraTypes = await API.get(API.DEVICE_TYPE);
    const typesField = formFields.value.find(f => f.key === 'device_type');
    if (typesField) {
      typesField.options = integraTypes.map((intType: string) => ({
        label: intType.name,
        value: intType.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching user types:', error);
  }
};

// Method to fetch sex values from the API
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
  //await fetchTypes();
  //await fetchSex();
  //setAffiliation();
  await fetchTypes();
  await fetchWorkspaces();
  loaded.value = true;
  emit('loaded');
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