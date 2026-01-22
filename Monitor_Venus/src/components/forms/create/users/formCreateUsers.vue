<template>
  <ion-page>
    <ion-header class="form-header-sticky ion-no-border">
      <ion-toolbar>
        <ion-title>Agregar {{ label }}</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="emit('closed')">
            <ion-icon :icon="icons.close" slot="icon-only"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-card-content>
        <form @submit.prevent="createUser">
          <ion-list>
            <!-- Name and Last Name -->
            <div :class="isMobile ? 'flex-column' : 'flex'">
              <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-1 mr-2'">
                <ion-label position="stacked" class="!mb-2">Nombre</ion-label>
                <ion-input
                  v-model="formValues.name"
                  type="text"
                  placeholder="Nombre"
                  class="custom"
                  fill="solid"
                ></ion-input>
              </ion-item>
              
              <ion-item :class="isMobile ? 'custom full-width' : 'custom flex-1 ml-2'">
                <ion-label position="stacked" class="!mb-2">Apellido</ion-label>
                <ion-input
                  v-model="formValues.last_name"
                  type="text"
                  placeholder="Apellido"
                  class="custom"
                  fill="solid"
                ></ion-input>
              </ion-item>
            </div>

            <!-- Code -->
            <ion-item class="custom">
              <ion-label position="stacked" class="!mb-2">Código de empleado</ion-label>
              <ion-input
                v-model="formValues.code"
                type="text"
                placeholder="EMP001"
                class="custom"
                fill="solid"
              ></ion-input>
            </ion-item>

            <!-- Username -->
            <ion-item class="custom">
              <ion-label position="stacked" class="!mb-2">Usuario</ion-label>
              <ion-input
                v-model="formValues.username"
                type="text"
                placeholder="nombre.usuario"
                class="custom"
                fill="solid"
              ></ion-input>
            </ion-item>

            <!-- Email -->
            <ion-item class="custom">
              <ion-label position="stacked" class="!mb-2">Correo electrónico</ion-label>
              <ion-input
                v-model="formValues.email"
                type="email"
                placeholder="ejemplo@mail.com"
                class="custom"
                fill="solid"
              ></ion-input>
            </ion-item>

            <!-- Phone Code and Phone -->
            <ion-item class="custom">
              <div :class="isMobile ? 'flex-column' : 'flex'">
                <div :class="isMobile ? 'full-width mb-4' : 'flex-0 mr-2'">
                  <ion-label position="stacked" class="!mb-2">Indicativo</ion-label>
                  <ModalSelector
                    v-model="selectedPhoneCode"
                    :options="countries"
                    value-field="phoneCode"
                    :display-field="country => `${country.phoneCode}`"
                    :search-fields="['name', 'phoneCode']"
                    title="Seleccionar Indicativo"
                    placeholder="Selecciona un indicativo"
                    search-placeholder="Buscar país..."
                  >
                    <template #display="{ selected }">
                      <span :class="`fi fi-${selected?.code.toLowerCase()}`" class="flag-icon"></span>
                      <span>{{ selected?.phoneCode }}</span>
                    </template>
                    
                    <template #option="{ option }">
                      <span :class="`fi fi-${option.code.toLowerCase()}`" class="flag-icon" slot="start"></span>
                      <ion-label>{{ option.name }} ({{ option.phoneCode }})</ion-label>
                    </template>
                  </ModalSelector>
                </div>
                <div :class="isMobile ? 'full-width' : 'flex-2 ml-2'">
                  <ion-label position="stacked" class="!mb-2">Teléfono</ion-label>
                  <ion-input
                    v-model="formValues.phone"
                    type="tel"
                    placeholder="000000000"
                    class="custom"
                    fill="solid"
                  ></ion-input>
                </div>
              </div>
            </ion-item>

            <!-- Country, State, City -->
            <div :class="isMobile ? 'flex-column' : 'flex'">
              <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-2 mr-2 !pl-0 !pr-0'">
                <ion-label position="stacked" class="!mb-2">País</ion-label>
                <ModalSelector
                  v-model="selectedCountry"
                  :options="countries"
                  value-field="name"
                  display-field="name"
                  :search-fields="['name']"
                  title="Selecciona tu país"
                  placeholder=" -"
                  search-placeholder="Buscar país..."
                >
                  <template #option="{ option }">
                    <span :class="`fi fi-${option.code.toLowerCase()}`" class="flag-icon" slot="start"></span>
                    <ion-label>{{ option.name }}</ion-label>
                  </template>
                </ModalSelector>
              </ion-item>

              <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-2 mr-2 !pl-0 !pr-0'">
                <ion-label position="stacked" class="!mb-2">Estado/Provincia</ion-label>
                <ModalSelector
                  v-model="selectedState"
                  :options="availableStates"
                  :display-field="state => state"
                  title="Selecciona tu estado"
                  placeholder=" -"
                  search-placeholder="Buscar estado..."
                  :disabled="!selectedCountry"
                />
              </ion-item>

              <ion-item :class="isMobile ? 'custom full-width' : 'custom flex-2 !pl-0 !pr-0'">
                <ion-label position="stacked" class="!mb-2">Ciudad</ion-label>
                <ModalSelector
                  v-model="selectedCity"
                  :options="availableCities"
                  :display-field="city => city"
                  title="Selecciona tu ciudad"
                  placeholder=" -"
                  search-placeholder="Buscar ciudad..."
                  :disabled="!selectedCountry || !selectedState"
                />
              </ion-item>
            </div>

            <!-- Address and Zip Code -->
            <div :class="isMobile ? 'flex-column' : 'flex'">
              <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-3 mr-2'">
                <ion-label position="stacked" class="!mb-2">Dirección</ion-label>
                <ion-input
                  v-model="formValues.address.address"
                  type="text"
                  placeholder="Calle Falsa #12-3"
                  class="custom"
                  fill="solid"
                ></ion-input>
              </ion-item>
              
              <ion-item :class="isMobile ? 'custom full-width' : 'custom flex-2'">
                <ion-label position="stacked" class="!mb-2">Código Postal</ion-label>
                <ion-input
                  v-model="formValues.address.zip_code"
                  type="text"
                  placeholder="000000"
                  class="custom"
                  fill="solid"
                ></ion-input>
              </ion-item>
            </div>
          </ion-list>
        </form>
      </ion-card-content>
    </ion-content>
    
    <ion-footer class="form-footer-sticky ion-no-border">
      <ion-toolbar>
        <div class="ion-text-end ion-padding">
          <ion-button type="submit" @click="createUser" :disabled="loading">
            <ion-spinner v-if="loading" slot="start"></ion-spinner>
            Guardar
          </ion-button>
        </div>
      </ion-toolbar>
    </ion-footer>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, inject } from 'vue';
import {
  IonPage,
  IonHeader,
  IonFooter,
  IonToolbar,
  IonTitle,
  IonContent,
  IonSpinner,
  IonCard,
  IonCardHeader,
  IonCardContent,
  IonList,
  IonItem,
  IonLabel,
  IonInput,
  IonButton,
  IonButtons,
  IonIcon,
} from '@ionic/vue';
import API from '@utils/api/api';
import ModalSelector from '@/components/ui/ModalSelector.vue';
import { countries } from '@/data/countries.js';
import { cities } from '@/data/cities.js';
import { useResponsiveView } from '@/composables/useResponsiveView.js';

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

// Responsive view
const { isMobile } = useResponsiveView(768);

// Icons
const icons = inject('icons', {});

// Form state
const loading = ref(false);
const loaded = ref(false);

// Reactive form values
const formValues = ref({
  name: '',
  last_name: '',
  code: '',
  username: '',
  email: '',
  phone: '',
  phone_code: '+57',
  country: '',
  address: {
    address: '',
    city: '',
    state: '',
    zip_code: ''
  }
});

// Separate reactive variables for selectors
const selectedPhoneCode = ref('+57');
const selectedCountry = ref('');
const selectedState = ref('');
const selectedCity = ref('');

// Watchers to sync selections with form values
watch(selectedPhoneCode, (newCode) => {
  formValues.value.phone_code = newCode;
});

watch(selectedCountry, (newVal) => {
  formValues.value.country = newVal;
  selectedState.value = '';
  selectedCity.value = '';
  formValues.value.address.state = '';
  formValues.value.address.city = '';
});

watch(selectedState, (newVal) => {
  formValues.value.address.state = newVal;
  selectedCity.value = '';
  formValues.value.address.city = '';
});

watch(selectedCity, (newVal) => {
  formValues.value.address.city = newVal;
});

// Computed properties for cascading selectors
const availableStates = computed(() => {
  const countryName = selectedCountry.value;
  if (!countryName) return [];
  const country = countries.find(c => c.name === countryName);
  if (!country) return [];
  const countryCode = country.code;
  const countryCities = cities[countryCode];
  if (!countryCities) return [];
  return Object.keys(countryCities);
});

const availableCities = computed(() => {
  const countryName = selectedCountry.value;
  const stateName = selectedState.value;
  if (!countryName || !stateName) return [];
  const country = countries.find(c => c.name === countryName);
  if (!country) return [];
  const countryCode = country.code;
  const countryCities = cities[countryCode];
  if (!countryCities) return [];
  const stateCities = countryCities[stateName] || [];
  return stateCities;
});

// Method to handle item creation success
const handleItemCreated = () => {
  emit('itemCreated');
};

// Create user function
const createUser = async () => {
  loading.value = true;
  try {
    console.log('🔑 Creating user with data:', formValues.value);

    // Prepare payload with nested address object
    const payload = {
      name: formValues.value.name,
      last_name: formValues.value.last_name,
      code: formValues.value.code,
      username: formValues.value.username,
      email: formValues.value.email,
      phone: formValues.value.phone,
      phone_code: formValues.value.phone_code,
      country: formValues.value.country,
      address: {
        address: formValues.value.address.address,
        city: formValues.value.address.city,
        state: formValues.value.address.state,
        zip_code: formValues.value.address.zip_code
      }
    };

    const response = await API.post(API.USER, payload);
    
    if (!response.error) {
      console.log('✅ User created successfully:', response);
      emit('itemCreated', formValues.value.name);
    } else {
      console.error('❌ Error creating user:', response.error);
    }
  } catch (error) {
    console.error('❌ Error creating user:', error);
  } finally {
    loading.value = false;
  }
};

// Run the data fetching and setup logic when the component is mounted
onMounted(async () => {
  loaded.value = true;
  emit('loaded');
});
</script>

<style scoped>
.flag-icon {
  margin-right: 8px;
  font-size: 1.2rem;
}

.flex {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.flex-column {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.flex-0 {
  flex: 0 0 auto;
  min-width: 120px;
}

.flex-1 {
  flex: 1;
}

.flex-2 {
  flex: 2;
}

.flex-3 {
  flex: 3;
}

.mr-2 {
  margin-right: 8px;
}

.ml-2 {
  margin-left: 8px;
}

.mb-4 {
  margin-bottom: 16px;
}

.full-width {
  width: 100%;
}

.divider {
  margin: 1rem 0;
  border-top: 1px solid var(--ion-color-light);
}
</style>