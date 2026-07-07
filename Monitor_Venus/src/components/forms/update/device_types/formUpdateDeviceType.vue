<template>
  <ion-page>
    <ion-content class="ion-padding">
      <form-update
        v-if="loaded"
        :type="type"
        :index="index"
        :fields="fields"
        :label="label"
        :additionalData="additionalData"
        :initialData="initialData"
        @itemEdited="handleitemEdited"
        @closed="emit('closed')"
      />
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

// Method to handle item creation success
const handleitemEdited = () => {
  emit('itemEdited');
};

// Run the data fetching and setup logic when the component is mounted
onMounted(async () => {
  loaded.value = true;
  emit('loaded');
});


</script>