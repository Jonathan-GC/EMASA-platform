<template>
  <ion-page>
    <ion-content class="ion-padding">
      <FormCreate
          :type="type"
          :fields="fields"
          :label="label"
          :additionalData="additionalData"
          @itemCreated="handleItemCreated"
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

const emit = defineEmits(['itemCreated', 'loaded']);

const loaded = ref(false);
const additionalData = ref({});
const formFields = ref([...props.fields]); // Use a ref to make a copy of the fields prop

// Method to handle item creation success
const handleItemCreated = () => {
  emit('itemCreated');
};

// Method to fetch user types from the API
const fetchTypes = async () => {
  try {
    const headers = { 'API-VERSION': '1' };
    const integraTypes = await API.get(API.I, headers);
    const typesField = formFields.value.find(f => f.key === 'type');
    if (typesField) {
      typesField.options = integraTypes.map((intType: string) => ({
        label: intType,
        value: intType.toUpperCase(),
      }));
    }
  } catch (error) {
    console.error('Error fetching user types:', error);
  }
};

// Method to fetch sex values from the API
const fetchSex = async () => {
  try {
    const headers = { 'API-VERSION': '1' };
    const sexValues = await API.get(API.SEX_VALUES, headers);
    const sexField = formFields.value.find(f => f.key === 'sex');
    if (sexField) {
      sexField.options = sexValues.map((sexValue: string) => ({
        label: sexValue,
        value: sexValue.toUpperCase(),
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
  loaded.value = true;
  emit('loaded');
});
</script>