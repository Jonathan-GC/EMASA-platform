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
+      @fieldChanged="onFieldChanged"
    />
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  IonPage, IonHeader, IonToolbar, IonTitle,
  IonContent, IonSpinner,
} from '@ionic/vue';
import API from '@utils/api/api';
import { MEASUREMENT_PROFILES } from '@/data/measurementProfiles.js';

// ---------------------------------------------------
// Props & emits (unchanged)
// ---------------------------------------------------
const props = defineProps({
  label: { type: String, required: true },
  fields: { type: Array, default: () => [] },
  type:   { type: String, required: true },
});
const emit = defineEmits(['itemCreated', 'loaded', 'closed']);

// ---------------------------------------------------
// Reactive state
// ---------------------------------------------------
const route = useRoute();
const loaded = ref(false);
const additionalData = ref<Record<string, any>>({});
const formFields = ref([...props.fields]);               // copy of fields prop
const deviceId = computed(() => route.params.device_id);

// ---------------------------------------------------
// Helpers
// ---------------------------------------------------
const getRefField = () => formFields.value.find(f => f.key === 'ref');

// ---------------------------------------------------
// Populate the ref dropdown from measurement profiles
// ---------------------------------------------------
const populateMeasurementTypes = () => {
  const refField = getRefField();
  if (refField) {
    refField.options = MEASUREMENT_PROFILES.map(p => ({
      label: p.label,
      value: p.value,               // canonical ref
    }));
  }
};

// ---------------------------------------------------
// Insert device_id into additionalData (unchanged)
// ---------------------------------------------------
const setDevice = () => {
  additionalData.value = {
    ...additionalData.value,
    device_id: deviceId.value,
  };
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
      // Inject unit into additionalData (no hidden field needed)
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

// ---------------------------------------------------
// Device list fetch (unchanged)
// ---------------------------------------------------
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
    console.error('Error fetching devices:', error);
  }
};

// ---------------------------------------------------
//  Item created handler (unchanged)
// ---------------------------------------------------
const handleItemCreated = () => emit('itemCreated');

// ---------------------------------------------------
// Field change handler – we need this to capture the `ref` changes emitted by FormCreate
// ---------------------------------------------------
function onFieldChanged(key: string, value: any) {
  console.log('⚡ fieldChanged', key, value);
  if (key === 'ref') {
    // Update the internal ref field value so the watcher sees the change
    const refFld = getRefField();
    if (refFld) {
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


// ---------------------------------------------------
// Lifecycle – initialise everything
// ---------------------------------------------------
onMounted(async () => {
  setDevice();                // device_id
  populateMeasurementTypes(); // fill ref dropdown
  await fetchDevices();       // fill device selector
  loaded.value = true;
  emit('loaded');
});
</script>