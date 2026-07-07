<template>
  <div class="color-picker-container">
    <!-- Selected Color Display -->
    <div 
      class="color-display"
      @click="openPicker"
      :style="{ backgroundColor: modelValue }"
    >
      <div class="color-info">
        <span class="color-label">{{ label }}</span>
        <span class="color-value">{{ modelValue }}</span>
      </div>
      <ion-icon :icon="icons.colorPalette" class="picker-icon"></ion-icon>
    </div>

    <!-- Color Picker Modal (Mobile & Desktop) -->
    <ion-modal :is-open="isOpen" @did-dismiss="closePicker">
      <ion-header>
        <ion-toolbar>
          <ion-title>{{ title || 'Seleccionar Color' }}</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closePicker">
              <ion-icon :icon="icons.close" slot="icon-only"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>

      <ion-content class="ion-padding">
        <div class="picker-content">
          <!-- 2D Color Canvas -->
          <div class="canvas-section">
            <div 
              class="color-canvas"
              :style="{ backgroundColor: `hsl(${hsl.h}, 100%, 50%)` }"
              @mousedown="startCanvasDrag"
              @touchstart="startCanvasDrag"
              ref="canvasRef"
            >
              <div class="canvas-white-gradient">
                <div class="canvas-black-gradient">
                  <div 
                    class="canvas-pointer"
                    :style="{ 
                      left: `${hsl.s}%`, 
                      top: `${100 - hsl.l}%` 
                    }"
                  ></div>
                </div>
              </div>
            </div>

            <!-- Hue Slider -->
            <div class="hue-slider-container">
              <input
                type="range"
                min="0"
                max="360"
                v-model.number="hsl.h"
                @input="updateFromHSL"
                class="hue-slider"
              />
            </div>
          </div>

          <!-- Color Preview with Hex -->
          <div class="preview-section">
            <div class="color-info-row">
              <div 
                class="color-preview-box"
                :style="{ backgroundColor: selectedColor }"
              ></div>
              <div class="color-details">
                <ion-item class="custom hex-item">
                  <ion-input
                    v-model="hexInput"
                    @ion-input="updateFromHex"
                    placeholder="#000000"
                    class="custom hex-input"
                  />
                </ion-item>
              </div>
            </div>
          </div>

          <!-- Predefined Color Palette -->
          <div class="palette-section" v-if="showPalette">
            <div class="color-grid">
              <div
                v-for="color in colorPalette"
                :key="color"
                class="color-swatch"
                :class="{ 'selected': selectedColor === color }"
                :style="{ backgroundColor: color }"
                @click="selectColor(color)"
              >
                <ion-icon 
                  v-if="selectedColor === color"
                  :icon="icons.checkmark"
                  class="check-icon"
                ></ion-icon>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="action-buttons">
            <ion-button fill="outline" @click="closePicker">
              Cancelar
            </ion-button>
            <ion-button @click="confirmColor" color="primary">
              <ion-icon :icon="icons.checkmark" slot="start"></ion-icon>
              Aplicar Color
            </ion-button>
          </div>
        </div>
      </ion-content>
    </ion-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject, onMounted } from 'vue'
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonIcon,
  IonContent,
  IonItem,
  IonLabel,
  IonInput
} from '@ionic/vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '#5865F2'
  },
  label: {
    type: String,
    default: 'Color'
  },
  title: {
    type: String,
    default: 'Seleccionar Color'
  },
  showPalette: {
    type: Boolean,
    default: true
  },
  colorPalette: {
    type: Array,
    default: () => [
      '#5865F2', '#57F287', '#FEE75C', '#EB459E',
      '#ED4245', '#F26522', '#99AAB5', '#23272A',
      '#9B59B6', '#3498DB', '#E91E63', '#00BCD4',
      '#4CAF50', '#FF9800', '#795548', '#607D8B',
      '#E53935', '#D81B60', '#8E24AA', '#5E35B1',
      '#3949AB', '#1E88E5', '#039BE5', '#00ACC1'
    ]
  },
  supportsAlpha: {
    type: Boolean,
    default: false
  },
  showRGB: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const icons = inject('icons', {})

// State
const isOpen = ref(false)
const selectedColor = ref(props.modelValue)
const hexInput = ref(props.modelValue)
const hsl = ref({ h: 0, s: 100, l: 50 })
const rgb = ref({ r: 0, g: 0, b: 0 })
const canvasRef = ref(null)
const isDragging = ref(false)

// Methods
const openPicker = () => {
  isOpen.value = true
  selectedColor.value = props.modelValue
  hexInput.value = props.modelValue
  hexToHSL(props.modelValue)
  hexToRGB(props.modelValue)
}

const closePicker = () => {
  isOpen.value = false
}

const confirmColor = () => {
  emit('update:modelValue', selectedColor.value)
  emit('change', selectedColor.value)
  closePicker()
}

const selectColor = (color) => {
  selectedColor.value = color
  hexInput.value = color
  hexToHSL(color)
  hexToRGB(color)
}

// Color Conversion Functions
const hexToHSL = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return
  
  let r = parseInt(result[1], 16) / 255
  let g = parseInt(result[2], 16) / 255
  let b = parseInt(result[3], 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h, s, l = (max + min) / 2

  if (max === min) {
    h = s = 0
  } else {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break
      case g: h = ((b - r) / d + 2) / 6; break
      case b: h = ((r - g) / d + 4) / 6; break
    }
  }

  hsl.value = {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100)
  }
}

const hexToRGB = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return
  
  rgb.value = {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  }
}

const hslToHex = (h, s, l) => {
  l /= 100
  const a = s * Math.min(l, 1 - l) / 100
  const f = n => {
    const k = (n + h / 30) % 12
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1)
    return Math.round(255 * color).toString(16).padStart(2, '0')
  }
  return `#${f(0)}${f(8)}${f(4)}`
}

const updateFromHSL = () => {
  const hex = hslToHex(hsl.value.h, hsl.value.s, hsl.value.l)
  selectedColor.value = hex
  hexInput.value = hex
  hexToRGB(hex)
}

const updateFromHex = (event) => {
  let hex = event.target.value
  if (!hex.startsWith('#')) hex = '#' + hex
  
  if (/^#[0-9A-F]{6}$/i.test(hex)) {
    selectedColor.value = hex
    hexToHSL(hex)
    hexToRGB(hex)
  }
}

// Canvas interaction
const startCanvasDrag = (event) => {
  isDragging.value = true
  updateCanvasColor(event)
  
  const moveHandler = (e) => {
    if (isDragging.value) {
      updateCanvasColor(e)
    }
  }
  
  const endHandler = () => {
    isDragging.value = false
    document.removeEventListener('mousemove', moveHandler)
    document.removeEventListener('mouseup', endHandler)
    document.removeEventListener('touchmove', moveHandler)
    document.removeEventListener('touchend', endHandler)
  }
  
  document.addEventListener('mousemove', moveHandler)
  document.addEventListener('mouseup', endHandler)
  document.addEventListener('touchmove', moveHandler)
  document.addEventListener('touchend', endHandler)
}

const updateCanvasColor = (event) => {
  if (!canvasRef.value) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = (event.touches ? event.touches[0].clientX : event.clientX) - rect.left
  const y = (event.touches ? event.touches[0].clientY : event.clientY) - rect.top
  
  const saturation = Math.max(0, Math.min(100, (x / rect.width) * 100))
  const lightness = Math.max(0, Math.min(100, 100 - (y / rect.height) * 100))
  
  hsl.value.s = Math.round(saturation)
  hsl.value.l = Math.round(lightness)
  
  updateFromHSL()
}

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  selectedColor.value = newValue
  hexInput.value = newValue
  hexToHSL(newValue)
  hexToRGB(newValue)
})

// Initialize
onMounted(() => {
  hexToHSL(props.modelValue)
  hexToRGB(props.modelValue)
})
</script>

<style scoped>
.color-picker-container {
  width: 100%;
}

.color-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid rgba(0, 0, 0, 0.1);
  min-height: 60px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.color-display:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.color-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: white;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.color-label {
  font-size: 0.85rem;
  opacity: 0.9;
  font-weight: 500;
}

.color-value {
  font-size: 1.1rem;
  font-weight: 700;
  font-family: 'Courier New', monospace;
}

.picker-icon {
  font-size: 28px;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.picker-content {
  max-width: 500px;
  margin: 0 auto;
}

/* 2D Canvas Section */
.canvas-section {
  margin-bottom: 1.5rem;
}

.color-canvas {
  width: 100%;
  height: 280px;
  border-radius: 12px;
  position: relative;
  cursor: crosshair;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  touch-action: none;
}

.canvas-white-gradient {
  width: 100%;
  height: 100%;
  background: linear-gradient(to right, #fff, transparent);
}

.canvas-black-gradient {
  width: 100%;
  height: 100%;
  background: linear-gradient(to top, #000, transparent);
  position: relative;
}

.canvas-pointer {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 3px solid white;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.3), 0 2px 8px rgba(0, 0, 0, 0.3);
  pointer-events: none;
}

.hue-slider-container {
  margin-top: 12px;
}

.hue-slider {
  width: 100%;
  height: 20px;
  border-radius: 10px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(to right, 
    hsl(0, 100%, 50%),
    hsl(60, 100%, 50%),
    hsl(120, 100%, 50%),
    hsl(180, 100%, 50%),
    hsl(240, 100%, 50%),
    hsl(300, 100%, 50%),
    hsl(360, 100%, 50%)
  );
}

/* Preview Section */
.preview-section {
  margin-bottom: 1.5rem;
}

.color-info-row {
  display: flex;
  gap: 12px;
  align-items: stretch;
}

.color-preview-box {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.color-details {
  flex: 1;
}

.palette-section {
  margin-bottom: 1.5rem;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
  gap: 8px;
}

.color-swatch {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid transparent;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.color-swatch:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.color-swatch.selected {
  border-color: var(--ion-color-dark);
  box-shadow: 0 0 0 2px white, 0 0 0 4px var(--ion-color-dark);
  transform: scale(1.05);
}

.check-icon {
  font-size: 24px;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
}

.slider-group {
  margin-bottom: 1.5rem;
}

.slider-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ion-color-dark);
}

.slider-label ion-icon {
  font-size: 18px;
  color: var(--ion-color-primary);
}

.slider-value {
  margin-left: auto;
  font-family: 'Courier New', monospace;
  color: var(--ion-color-medium);
}

input[type="range"] {
  width: 100%;
  height: 32px;
  border-radius: 8px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.hue-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.3), 0 2px 6px rgba(0, 0, 0, 0.3);
}

.hue-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.3), 0 2px 6px rgba(0, 0, 0, 0.3);
}

.hex-item {
  --background: var(--ion-color-light-tint);
  border-radius: 8px;
  --padding-start: 12px;
  --padding-end: 12px;
}

.hex-input {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 1.1rem;
  text-align: center;
  text-transform: uppercase;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.action-buttons ion-button {
  flex: 1;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .color-grid {
    grid-template-columns: repeat(6, 1fr);
  }

  .rgb-values {
    flex-direction: column;
  }
}
</style>
