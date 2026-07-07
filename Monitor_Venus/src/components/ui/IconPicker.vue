<template>
  <div class="icon-picker-wrapper">
    <ion-button 
      @click="openModal" 
      expand="block" 
      fill="outline"
      :disabled="disabled"
    >
      <div class="selected-icon-display">
        <ion-icon v-if="modelValue" :icon="getIconByName(modelValue)" class="preview-icon"></ion-icon>
        <span>{{ modelValue || placeholder }}</span>
      </div>
    </ion-button>

    <ion-modal :is-open="isOpen" @didDismiss="closeModal">
      <ion-page>
        <ion-header class="custom">
          <ion-toolbar>
            <ion-title>{{ title }}</ion-title>
            <ion-buttons slot="end">
              <ion-button @click="closeModal">
                <ion-icon :icon="icons.close"></ion-icon>
              </ion-button>
            </ion-buttons>
          </ion-toolbar>
          <ion-toolbar v-if="searchable">
            <ion-searchbar
              class="custom"
              v-model="searchQuery"
              placeholder="Buscar icono..."
              :debounce="300"
              @ionInput="handleSearch"
            ></ion-searchbar>
          </ion-toolbar>
        </ion-header>

        <ion-content class="ion-padding">
          <div v-if="filteredIcons.length === 0" class="no-results">
            <p>No se encontraron iconos</p>
          </div>
          <div v-else class="icons-grid">
            <div
              v-for="(icon, name) in filteredIcons"
              :key="name"
              class="icon-item"
              :class="{ 'selected': modelValue === name }"
              @click="selectIcon(name)"
            >
              <ion-icon :icon="icon" class="icon-display"></ion-icon>
              <span class="icon-name">{{ name }}</span>
            </div>
          </div>
        </ion-content>

        <ion-footer v-if="modelValue">
          <ion-toolbar>
            <ion-button 
              expand="block" 
              @click="clearSelection"
              fill="clear"
              color="danger"
            >
            <ion-icon :icon="icons.delete" slot="icon-only" />
              Limpiar selección
            </ion-button>
          </ion-toolbar>
        </ion-footer>
      </ion-page>
    </ion-modal>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue';
import {
  IonButton,
  IonModal,
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonIcon,
  IonContent,
  IonSearchbar,
  IonFooter,
} from '@ionic/vue';
import { icons as iconRegistry } from '@/plugins/icons/icons';

const props = defineProps({
  modelValue: {
    type: String,
    default: null,
  },
  title: {
    type: String,
    default: 'Seleccionar Icono',
  },
  placeholder: {
    type: String,
    default: 'Seleccionar icono...',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  searchable: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['update:modelValue']);

const icons = inject('icons', {});
const isOpen = ref(false);
const searchQuery = ref('');

const filteredIcons = computed(() => {
  if (!searchQuery.value) {
    return iconRegistry;
  }
  
  const query = searchQuery.value.toLowerCase();
  const filtered = {};
  
  Object.entries(iconRegistry).forEach(([name, icon]) => {
    if (name.toLowerCase().includes(query)) {
      filtered[name] = icon;
    }
  });
  
  return filtered;
});

const openModal = () => {
  if (!props.disabled) {
    isOpen.value = true;
  }
};

const closeModal = () => {
  isOpen.value = false;
  searchQuery.value = '';
};

const selectIcon = (iconName) => {
  emit('update:modelValue', iconName);
  closeModal();
};

const clearSelection = () => {
  emit('update:modelValue', null);
  closeModal();
};

const getIconByName = (name) => {
  return iconRegistry[name] || null;
};

const handleSearch = (event) => {
  searchQuery.value = event.target.value;
};
</script>

<style scoped>
.icon-picker-wrapper {
  width: 100%;
}

.selected-icon-display {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  justify-content: center;
}

.preview-icon {
  font-size: 24px;
}

.icons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 16px;
  padding: 16px 0;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  border: 2px solid var(--ion-color-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--ion-color-light);
}

.icon-item:hover {
  border-color: var(--ion-color-primary);
  background: var(--ion-color-primary-tint);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.icon-item.selected {
  border-color: var(--ion-color-primary);
  background: var(--ion-color-primary);
  color: white;
}

.icon-display {
  font-size: 32px;
  margin-bottom: 8px;
}

.icon-name {
  font-size: 12px;
  text-align: center;
  word-break: break-word;
  max-width: 100%;
}

.no-results {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--ion-color-medium);
}

.no-results p {
  font-size: 16px;
}
</style>
