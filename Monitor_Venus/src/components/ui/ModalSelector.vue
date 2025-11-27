<template>
  <div>
    <!-- Clickable Button -->
    <div 
      @click="openModal"
      class="modal-selector-button bg-zinc-300 rounded-md custom country-selector-button"
      :class="{ 'disabled': disabled }"
    >
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-2">
          <slot name="display" :selected="selectedOption">
            <span v-if="selectedOption">{{ getDisplayText(selectedOption) }}</span>
            <span v-else class="text-gray-500">{{ placeholder || 'Seleccionar...' }}</span>
          </slot>
        </div>
        <ion-icon :icon="chevronDownIcon" class="dropdown-icon"></ion-icon>
      </div>
    </div>

    <!-- Modal -->
    <ion-modal :is-open="isOpen" @did-dismiss="closeModal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>{{ title }}</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeModal">
              <ion-icon :icon="closeIcon" slot="icon-only"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
        
        <!-- Search Bar -->
        <ion-toolbar v-if="searchable">
          <ion-searchbar
            class="rounded-xl custom"
            v-model="searchQuery"
            :placeholder="searchPlaceholder || 'Buscar...'"
            @ionInput="onSearch"
            animated
          ></ion-searchbar>
        </ion-toolbar>
      </ion-header>
      
      <ion-content>
        <ion-list>
          <ion-item
            v-for="(option, index) in filteredOptions"
            :key="getOptionKey(option, index)"
            button
            @click="selectOption(option)"
            :class="{ 'selected': isSelected(option) }"
          >
            <slot name="option" :option="option">
              <ion-label>{{ getDisplayText(option) }}</ion-label>
            </slot>
          </ion-item>
          
          <!-- No results message -->
          <ion-item v-if="filteredOptions.length === 0">
            <ion-label class="text-center text-gray-500">
              {{ noResultsText || 'No se encontraron resultados' }}
            </ion-label>
          </ion-item>
        </ion-list>
      </ion-content>
    </ion-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonIcon,
  IonContent,
  IonList,
  IonItem,
  IonLabel,
  IonSearchbar
} from '@ionic/vue'
import { chevronDown, close } from 'ionicons/icons'

const props = defineProps({
  // Current selected value
  modelValue: {
    type: [String, Number, Object],
    default: null
  },
  
  // Array of options to display
  options: {
    type: Array,
    required: true
  },
  
  // Modal title
  title: {
    type: String,
    default: 'Seleccionar'
  },
  
  // Placeholder text
  placeholder: {
    type: String,
    default: 'Seleccionar...'
  },
  
  // Field to display (if options are objects)
  displayField: {
    type: [String, Function],
    default: null
  },
  
  // Field to use as unique key (if options are objects)
  valueField: {
    type: String,
    default: null
  },
  
  // Enable search functionality
  searchable: {
    type: Boolean,
    default: true
  },
  
  // Search placeholder
  searchPlaceholder: {
    type: String,
    default: 'Buscar...'
  },
  
  // Fields to search in (array of field names)
  searchFields: {
    type: Array,
    default: () => []
  },
  
  // Custom search function
  searchFunction: {
    type: Function,
    default: null
  },
  
  // No results message
  noResultsText: {
    type: String,
    default: 'No se encontraron resultados'
  },
  
  // Disable the selector
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'select'])

// State
const isOpen = ref(false)
const searchQuery = ref('')

// Icons
const chevronDownIcon = chevronDown
const closeIcon = close

// Computed
const selectedOption = computed(() => {
  if (!props.modelValue) return null
  
  if (props.valueField) {
    return props.options.find(opt => opt[props.valueField] === props.modelValue)
  }
  
  return props.options.find(opt => opt === props.modelValue) || props.modelValue
})

const filteredOptions = computed(() => {
  if (!searchQuery.value || !props.searchable) {
    return props.options
  }
  
  const query = searchQuery.value.toLowerCase().trim()
  
  // Use custom search function if provided
  if (props.searchFunction) {
    return props.options.filter(opt => props.searchFunction(opt, query))
  }
  
  // Default search implementation
  return props.options.filter(option => {
    // If option is a primitive value
    if (typeof option !== 'object') {
      return String(option).toLowerCase().includes(query)
    }
    
    // If searchFields are specified, search in those fields
    if (props.searchFields.length > 0) {
      return props.searchFields.some(field => {
        const value = option[field]
        return value && String(value).toLowerCase().includes(query)
      })
    }
    
    // If displayField is specified, search in that field
    if (props.displayField && typeof props.displayField === 'string') {
      const value = option[props.displayField]
      return value && String(value).toLowerCase().includes(query)
    }
    
    // Fallback: search in all fields
    return Object.values(option).some(value => 
      value && String(value).toLowerCase().includes(query)
    )
  })
})

// Methods
const openModal = () => {
  if (!props.disabled) {
    isOpen.value = true
  }
}

const closeModal = () => {
  isOpen.value = false
  searchQuery.value = ''
}

const selectOption = (option) => {
  const value = props.valueField ? option[props.valueField] : option
  emit('update:modelValue', value)
  emit('select', option)
  closeModal()
}

const isSelected = (option) => {
  if (!props.modelValue) return false
  
  if (props.valueField) {
    return option[props.valueField] === props.modelValue
  }
  
  return option === props.modelValue
}

const getDisplayText = (option) => {
  if (!option) return ''
  
  // If displayField is a function, call it
  if (typeof props.displayField === 'function') {
    return props.displayField(option)
  }
  
  // If displayField is a string, get that property
  if (props.displayField && typeof option === 'object') {
    return option[props.displayField]
  }
  
  // If option is primitive, return it
  if (typeof option !== 'object') {
    return option
  }
  
  // Fallback: try common field names
  return option.name || option.label || option.title || String(option)
}

const getOptionKey = (option, index) => {
  if (props.valueField && typeof option === 'object') {
    return option[props.valueField]
  }
  return index
}

const onSearch = (event) => {
  searchQuery.value = event.target.value
}

// Watch for modal close to reset search
watch(isOpen, (newValue) => {
  if (!newValue) {
    searchQuery.value = ''
  }
})
</script>
