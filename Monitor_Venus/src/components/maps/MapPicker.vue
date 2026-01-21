<template>
  <ion-modal :is-open="show" @didDismiss="onClose" class="map-picker-modal">
    <ion-header>
      <ion-toolbar>
        <ion-title>{{ title || 'Seleccionar ubicación' }}</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="close">Cerrar</ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content>
      <div ref="mapEl" class="map-root"></div>

      <div class="coords-bar">
        <div class="coords-display">
          <div class="coord-item">
            <span class="label">Lat:</span>
            <span class="value">{{ coords.lat.toFixed(6) }}</span>
          </div>
          <div class="coord-item">
            <span class="label">Lng:</span>
            <span class="value">{{ coords.lng.toFixed(6) }}</span>
          </div>
        </div>
        <ion-button @click="confirm" color="primary">
          Confirmar ubicación
        </ion-button>
      </div>
    </ion-content>
  </ion-modal>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonContent
} from '@ionic/vue'
import L from 'leaflet'

// Fix for default marker icons not showing in Vite/Vue
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const props = defineProps({
  show: { type: Boolean, default: false },
  initial: { type: Object, default: null }, // { lat, lng }
  zoom: { type: Number, default: 13 },
  title: { type: String, default: '' }
})

const emit = defineEmits(['update:show', 'selected'])

const mapEl = ref(null)
let map = null
let marker = null

const coords = ref({ lat: 0, lng: 0 })

// Configure default icon
const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIconRetina,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

function initMap() {
  if (!mapEl.value || map) return

  const initialCenter = props.initial && props.initial.lat && props.initial.lng 
    ? [props.initial.lat, props.initial.lng] 
    : [0, 0]
    
  coords.value = props.initial && props.initial.lat && props.initial.lng
    ? { ...props.initial }
    : { lat: 0, lng: 0 }

  map = L.map(mapEl.value).setView(initialCenter, props.zoom)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)

  marker = L.marker(initialCenter, { 
    draggable: true,
    icon: DefaultIcon
  }).addTo(map)

  map.on('click', (e) => {
    marker.setLatLng(e.latlng)
    coords.value = { lat: e.latlng.lat, lng: e.latlng.lng }
  })

  marker.on('dragend', (e) => {
    const p = e.target.getLatLng()
    coords.value = { lat: p.lat, lng: p.lng }
  })
  
  // Trigger a resize to fix grey area issues in modals
  setTimeout(() => {
    map.invalidateSize()
  }, 400)
}

watch(() => props.show, async (v) => {
  if (v) {
    await nextTick()
    setTimeout(initMap, 300)
  } else {
    if (map) {
      map.remove()
      map = null
      marker = null
    }
  }
})

function close() {
  emit('update:show', false)
}

function onClose() {
  emit('update:show', false)
}

function confirm() {
  emit('selected', { ...coords.value })
  close()
}

onUnmounted(() => {
  if (map) map.remove()
})
</script>

<style scoped>
.map-root {
  height: 70vh;
  width: 100%;
  border-bottom: 1px solid var(--ion-color-step-200);
}

.coords-bar {
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 16px;
  background: var(--ion-background-color);
}

.coords-display {
  display: flex;
  justify-content: space-around;
  background: var(--ion-color-light);
  padding: 12px;
  border-radius: 8px;
}

.coord-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.coord-item .label {
  font-size: 11px;
  text-transform: uppercase;
  color: var(--ion-color-step-500);
  font-weight: 600;
}

.coord-item .value {
  font-family: monospace;
  font-size: 16px;
  font-weight: bold;
}

@media (min-width: 768px) {
  .coords-bar {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
  
  .coords-display {
    flex: 1;
    margin-right: 20px;
    justify-content: flex-start;
    gap: 40px;
  }
}
</style>
