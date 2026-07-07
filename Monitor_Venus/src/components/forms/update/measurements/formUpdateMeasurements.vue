<template>
  <ion-page>
    <ion-content class="ion-padding">
      <FormUpdate
          :type="type"
          :index="index"
          :fields="formFields"
          :label="label"
          :additionalData="additionalData"
          :initialData="initialData"
          :reqIndex="false"
          @itemEdited="handleItemEdited"
          @closed="emit('closed')"
      />
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
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
  index: {
    type: Number,
  }, 
  initialData: {
    type: Object,
    default: () => ({}),
  } 
});

const emit = defineEmits(['itemCreated', 'loaded', 'closed']);

// Get route to access deviceId from params
const route = useRoute();

const loaded = ref(false);
const additionalData = ref({});
const formFields = ref([...props.fields]); // Use a ref to make a copy of the fields prop

// Get deviceId from route params and set as additional data
const deviceId = computed(() => route.params.deviceId || route.params.device_id);

// Set device_id in additionalData for the form endpoint
onMounted(() => {
  if (deviceId.value) {
    additionalData.value = {
      ...additionalData.value,
      device_id: deviceId.value
    };
    console.log('Device ID set for measurements:', deviceId.value);
  }
});

// Method to handle item creation success
const handleItemEdited = () => {
  emit('itemEdited');
};

// Method to fetch user types from the API
const fetchDevices = async () => {
  try {
    const devices = await API.get(API.DEVICE);
    const devicesField = formFields.value.find(f => f.key === 'device');
    if (devicesField) {
      devicesField.options = devices.map((intType: string) => ({
        label: intType.name,
        value: intType.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching user types:', error);
  }
};



// Method to set additional data for the form
const setDevice = () => {
  additionalData.value = {
    ...additionalData.value,
    device: route.params.device_id
  };
  console.log("Additional Data Set:", additionalData.value);
};

// Run the data fetching and setup logic when the component is mounted
onMounted(async () => {
  //await fetchTypes();
  //await fetchSex();
  //setAffiliation();
  setDevice();
  await fetchDevices();
  loaded.value = true;
  emit('loaded');
});
</script>