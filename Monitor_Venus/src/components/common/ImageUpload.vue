<!--
  ImageUpload Component
  
  A reusable image upload component with preview, validation, and error handling.
  
  Usage:
  <ImageUpload
    v-model="imageUrl"
    :max-size="5 * 1024 * 1024"
    placeholder-text="Click to select an image"
    @change="handleImageChange"
    @error="handleImageError"
  />
  
  Props:
  - modelValue: String - The image preview URL (v-model)
  - accept: String - File types to accept (default: 'image/*')
  - maxSize: Number - Maximum file size in bytes (default: 5MB)
  - icon: String - Custom icon for placeholder
  - placeholderText: String - Custom placeholder text
  - alt: String - Alt text for image
  - removeButtonText: String - Text for remove button (default: 'Remover')
  - removeButtonColor: String - Color for remove button (default: 'danger')
  - showActions: Boolean - Show action buttons (default: true)
  - disabled: Boolean - Disable the component (default: false)
  - validateImage: Boolean - Validate that file is an image (default: true)
  
  Events:
  - update:modelValue - Emitted when image changes (v-model)
  - change - Emitted with file info { file, preview, name, size, type }
  - error - Emitted when validation fails
  - remove - Emitted when image is removed
  
  Exposed Methods:
  - removeImage() - Programmatically remove the image
  - triggerFileInput() - Programmatically trigger file selection
  - getFileInfo() - Get current file information
-->
<template>
  <div class="image-upload-component">
    <div class="image-upload-container">
      <div class="image-preview" @click="triggerFileInput">
        <img 
          v-if="imagePreview" 
          :src="imagePreview" 
          :alt="alt || 'Image preview'" 
          class="uploaded-image"
        />
        <div v-else class="image-placeholder">
          <ion-icon :icon="icon || icons.camera" size="large"></ion-icon>
          <p>{{ placeholderText || 'Haz clic para seleccionar una imagen' }}</p>
        </div>
        
        <!-- Floating Remove Button -->
        <ion-button
          v-if="showActions && imagePreview"
          class="floating-remove-button"
          :color="removeButtonColor"
          shape="round"
          size="small"
          @click.stop="removeImage"
          :disabled="disabled"
        >
          <ion-icon :icon="icons.delete" slot="icon-only"></ion-icon>
        </ion-button>
      </div>
      <input
        ref="fileInputRef"
        type="file"
        :accept="accept"
        @change="handleFileChange"
        style="display: none"
      />
    </div>

    <div v-if="error" class="error-message">
      <ion-icon :icon="icons.alert" color="danger"></ion-icon>
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import { IonButton, IonIcon } from '@ionic/vue'

// Inject icons
const icons = inject('icons', {})

// Props
const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  accept: {
    type: String,
    default: 'image/*'
  },
  maxSize: {
    type: Number,
    default: 5 * 1024 * 1024 // 5MB by default
  },
  icon: {
    type: String,
    default: null
  },
  placeholderText: {
    type: String,
    default: null
  },
  alt: {
    type: String,
    default: null
  },
  removeButtonText: {
    type: String,
    default: 'Remover'
  },
  removeButtonColor: {
    type: String,
    default: 'danger'
  },
  showActions: {
    type: Boolean,
    default: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  validateImage: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'change', 'error', 'remove'])

// State
const fileInputRef = ref(null)
const imagePreview = ref(props.modelValue)
const error = ref(null)
const selectedFile = ref(null)

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  imagePreview.value = newValue
})

// Trigger file input
const triggerFileInput = () => {
  if (!props.disabled) {
    fileInputRef.value?.click()
  }
}

// Handle file change
const handleFileChange = (event) => {
  const file = event.target.files[0]
  error.value = null

  if (!file) return

  // Validate file size
  if (file.size > props.maxSize) {
    const sizeMB = (props.maxSize / (1024 * 1024)).toFixed(1)
    error.value = `El archivo es muy grande. Tamaño máximo: ${sizeMB}MB`
    emit('error', error.value)
    return
  }

  // Validate file type
  if (props.validateImage && !file.type.startsWith('image/')) {
    error.value = 'Por favor selecciona un archivo de imagen válido'
    emit('error', error.value)
    return
  }

  // Store the file
  selectedFile.value = file

  // Create preview
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target.result
    emit('update:modelValue', e.target.result)
    emit('change', {
      file: file,
      preview: e.target.result,
      name: file.name,
      size: file.size,
      type: file.type
    })
  }
  reader.onerror = () => {
    error.value = 'Error al leer el archivo'
    emit('error', error.value)
  }
  reader.readAsDataURL(file)
}

// Remove image
const removeImage = () => {
  imagePreview.value = null
  selectedFile.value = null
  error.value = null
  
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  
  emit('update:modelValue', null)
  emit('remove')
}

// Get file info
const getFileInfo = () => {
  return selectedFile.value ? {
    file: selectedFile.value,
    name: selectedFile.value.name,
    size: selectedFile.value.size,
    type: selectedFile.value.type,
    preview: imagePreview.value
  } : null
}

// Expose methods to parent
defineExpose({
  removeImage,
  triggerFileInput,
  getFileInfo
})
</script>

<style scoped>
.image-upload-component {
  width: 100%;
}

.image-upload-container {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.image-preview {
  position: relative;
  width: 200px;
  height: 200px;
  border: 3px dashed #cbd5e1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f8fafc;
}

.image-preview:hover {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.uploaded-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
  color: #64748b;
}

.image-placeholder ion-icon {
  font-size: 48px;
  margin-bottom: 12px;
  color: #94a3b8;
}

.image-placeholder p {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.4;
}

.floating-remove-button {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 40px;
  height: 40px;
  --padding-start: 0;
  --padding-end: 0;
  z-index: 10;

  margin: 0;
}

.floating-remove-button ion-icon {
  font-size: 20px;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 0.9rem;
}

.error-message ion-icon {
  flex-shrink: 0;
  font-size: 20px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .image-preview {
    width: 160px;
    height: 160px;
  }

  .image-placeholder ion-icon {
    font-size: 36px;
  }

  .image-placeholder p {
    font-size: 0.8rem;
  }

  .floating-remove-button {
    width: 36px;
    height: 36px;
    bottom: 0;
    right: 0;
  }

  .floating-remove-button ion-icon {
    font-size: 18px;
  }
}
</style>
