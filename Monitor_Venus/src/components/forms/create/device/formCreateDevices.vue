<template>
  <ion-page>
    <ion-content class="ion-padding">
      <FormCreate
          :type="type"
          :fields="formFields"
          :label="label"
          :additionalData="additionalData"
          @itemCreated="handleItemCreated"
          @closed="emit('closed')"
      />
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
});

const emit = defineEmits(['itemCreated', 'loaded', 'closed']);

const loaded = ref(false);
const additionalData = ref({});
const formFields = ref([...props.fields]); // Use a ref to make a copy of the fields prop

// Method to handle item creation success
const handleItemCreated = () => {
  emit('itemCreated');
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

const fetchType = async () => {
  try {
    const types = await API.get(API.DEVICE_TYPE);
    const typeField = formFields.value.find(f => f.key === 'device_type');
    if (typeField) {
      typeField.options = types.map((type: string) => ({
        label: type.name,
        value: type.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching workspaces:', error);
  }
};

const fetchApplications = async () => {
  try {
    const applications = await API.get(API.APPLICATION);
    const applicationField = formFields.value.find(f => f.key === 'application');
    if (applicationField) {
      applicationField.options = applications.map((application: string) => ({
        label: application.name,
        value: application.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching workspaces:', error);
  }
};

const fetchDeviceProfile = async () => {
  try {
    const types = await API.get(API.DEVICE_PROFILE);
    const typeField = formFields.value.find(f => f.key === 'device_profile');
    if (typeField) {
      typeField.options = types.map((type: string) => ({
        label: type.name,
        value: type.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching workspaces:', error);
  }
};

const fetchMachines = async () => {
  try {
    const types = await API.get(API.MACHINE);
    const typeField = formFields.value.find(f => f.key === 'machine');
    if (typeField) {
      typeField.options = types.map((type: string) => ({
        label: type.name,
        value: type.id,
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
  //await fetchTypes();
  //await fetchSex();
  //setAffiliation();
  await fetchMachines();
  await fetchType();
  await fetchApplications();
  await fetchDeviceProfile();
  await fetchWorkspaces();
  loaded.value = true;
  emit('loaded');
});
</script>