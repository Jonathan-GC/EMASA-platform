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


// Run the data fetching and setup logic when the component is mounted
onMounted(async () => {
  loaded.value = true;
  emit('loaded');
});
</script>