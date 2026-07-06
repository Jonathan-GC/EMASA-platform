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
          @fieldChanged="onFieldChanged"
      />
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
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
import { MEASUREMENT_PROFILES } from '@/data/measurementProfiles.js';

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


 const getRefField = () => formFields.value.find(f => f.key === 'ref');

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

// ---------------------------------------------------
// Field change handler – updates the internal `ref` field value
// ---------------------------------------------------
function onFieldChanged(key: string, value: any) {
  console.log('⚡ fieldChanged', key, value);
  if (key === 'ref') {
    const refFld = getRefField();
    if (refFld) {
      // Update the field object so the watcher below can see the change
      refFld.value = value;
    }
    // Also directly update additionalData with unit and label
    const profile = MEASUREMENT_PROFILES.find(p => p.value === value);
    if (profile) {
      console.log('✅ Found profile for ref', value, 'unit =', profile.unit, 'label =', profile.label);
      additionalData.value = {
        ...additionalData.value,
        unit: profile.unit,
        label: profile.label,
      };
    }
  }
}

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

// Method to fetch user types from the API
const fetchMeasurements = async () => {
  try {
    const measurementField = getRefField();
    if (measurementField) {
      measurementField.options = MEASUREMENT_PROFILES.map(p => ({
        label: p.label,
        value: p.value,
      }));
    }
  } catch (error) {
    console.error('Error fetching sex values:', error);
  }
};

// ---------------------------------------------------
// Watch the selected `ref` and auto‑inject the corresponding unit
// ---------------------------------------------------
watch(
  () => {
    const refField = getRefField();
    return refField?.value ?? null;
  },
  (newRef) => {
    console.log('🔎 ref changed →', newRef);
    if (!newRef) {
      console.log('⚪ No ref selected – removing unit from additionalData');
      const { unit, label, ...rest } = additionalData.value;
      additionalData.value = rest;
      return;
    }
    const profile = MEASUREMENT_PROFILES.find(p => p.value === newRef);
    if (profile) {
      console.log('✅ Found profile for ref', newRef, 'unit =', profile.unit, 'label =', profile.label);
      // Inject unit and label into additionalData (no hidden field needed)
      additionalData.value = { ...additionalData.value, unit: profile.unit, label: profile.label };
    } else {
      console.warn('⚠️ No profile found for ref', newRef, '- removing any unit');
      const { unit, label, ...rest } = additionalData.value;
      additionalData.value = rest;
    }
    console.log('📦 additionalData now:', additionalData.value);
  },
  { immediate: true }
);



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
  await fetchMeasurements();
  loaded.value = true;
  emit('loaded');
});
</script>