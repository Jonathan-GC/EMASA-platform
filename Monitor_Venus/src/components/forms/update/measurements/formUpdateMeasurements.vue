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
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { IonPage, IonContent } from '@ionic/vue';
import API from '@utils/api/api';
import { MEASUREMENT_PROFILES } from '@/data/measurementProfiles.js';

const props = defineProps({
  label: { type: String, required: true },
  fields: { type: Array, default: () => [] },
  type:  { type: String, required: true },
  index: { type: Number },
  initialData: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['itemEdited', 'loaded', 'closed']);

const route = useRoute();
const additionalData = ref<Record<string, any>>({});
const formFields = ref([...props.fields]);
const deviceId = computed(() => route.params.device_id);

const getRefField = () => formFields.value.find(f => f.key === 'ref');

const populateMeasurementTypes = () => {
  const refField = getRefField();
  if (refField) {
    refField.options = MEASUREMENT_PROFILES.map(p => ({
      label: p.label,
      value: p.value,
    }));
  }
};

const setDevice = () => {
  additionalData.value = { ...additionalData.value, device: deviceId.value };
};

function onFieldChanged(key: string, value: any) {
  if (key === 'ref') {
    const profile = MEASUREMENT_PROFILES.find(p => p.value === value);
    if (profile) {
      additionalData.value = {
        ...additionalData.value,
        unit: profile.unit,
        label: profile.label,
      };
    } else {
      const { unit, label, ...rest } = additionalData.value;
      additionalData.value = rest;
    }
  }
}

const fetchDevices = async () => {
  try {
    const devices = await API.get(API.DEVICE);
    const devicesField = formFields.value.find(f => f.key === 'device');
    if (devicesField) {
      devicesField.options = devices.map((d: any) => ({
        label: d.name,
        value: d.id,
      }));
    }
  } catch (error) {
    console.error('Error fetching devices:', error);
  }
};

const handleItemEdited = () => emit('itemEdited');

onMounted(async () => {
  setDevice();
  await fetchDevices();
  populateMeasurementTypes();
  emit('loaded');
});
</script>