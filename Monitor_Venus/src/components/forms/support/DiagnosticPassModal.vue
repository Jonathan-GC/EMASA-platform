<template>
  <ion-page>
    <ion-header class="custom">
      <ion-toolbar>
        <ion-title>Pase diagnóstico</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeModal">
            <ion-icon :icon="icons.close"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-item class="ticket-summary" lines="none">
        <ion-icon slot="start" :icon="icons.mail"></ion-icon>
        <ion-label>
          <h2>{{ props.ticket.title || '(Sin asunto)' }}</h2>
          <p>Otorga acceso temporal a un técnico sobre el espacio de trabajo del ticket.</p>
        </ion-label>
      </ion-item>

      <ion-note color="warning" class="warning-note">
        <ion-icon :icon="icons.warning"></ion-icon>
        El técnico podrá operar sobre el workspace seleccionado por la duración indicada. El acceso expira automáticamente y puede revocarse en cualquier momento.
      </ion-note>

      <div v-if="loading" class="ion-text-center ion-padding">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando datos...</p>
      </div>

      <div v-else-if="loadError" class="error-container ion-text-center">
        <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
        <p>{{ loadError }}</p>
        <ion-button @click="init" fill="outline">Reintentar</ion-button>
      </div>

      <div v-else>
        <ion-item>
          <ion-label position="stacked">Técnico</ion-label>
          <ion-select
            v-model="technicianId"
            :placeholder="technicians.length ? 'Selecciona un técnico' : 'No hay técnicos disponibles'"
            :disabled="!technicians.length || submitting"
          >
            <ion-select-option v-for="t in technicians" :key="t.id" :value="t.id">
              {{ t.full_name || t.name || `#${t.id}` }}
              <template v-if="t.role"> ({{ t.role }})</template>
            </ion-select-option>
          </ion-select>
        </ion-item>

        <ion-item>
          <ion-label position="stacked">Espacio de trabajo</ion-label>
          <ion-select
            v-model="workspaceId"
            :placeholder="workspaces.length ? 'Selecciona un workspace' : 'No hay workspaces disponibles'"
            :disabled="!workspaces.length || submitting"
          >
            <ion-select-option v-for="w in workspaces" :key="w.id" :value="w.id">
              {{ w.name || `#${w.id}` }}
            </ion-select-option>
          </ion-select>
        </ion-item>

        <ion-item>
          <ion-label position="stacked">Duración (horas)</ion-label>
          <ion-input v-model="durationHours" type="number" min="1" max="720" :disabled="submitting" placeholder="4"></ion-input>
        </ion-item>

        <ion-item>
          <ion-label position="stacked">Motivo</ion-label>
          <ion-textarea v-model="reason" rows="3" :disabled="submitting" placeholder="Motivo del pase diagnóstico"></ion-textarea>
        </ion-item>

        <div class="ion-padding-top">
          <ion-button
            expand="block"
            :disabled="!technicianId || !workspaceId || !durationHours || submitting"
            @click="confirmGrant"
            color="primary"
          >
            <ion-spinner v-if="submitting" name="crescent" slot="start"></ion-spinner>
            <ion-icon v-else :icon="icons.shield" slot="start"></ion-icon>
            Emitir pase diagnóstico
          </ion-button>
        </div>

        <div class="divider"></div>

        <div v-if="passesLoading" class="ion-text-center ion-padding">
          <ion-spinner name="dots"></ion-spinner>
          <p>Cargando pases activos...</p>
        </div>

        <div v-else-if="activePasses.length" class="passes-section">
          <h3 class="passes-title">
            <ion-icon :icon="icons.time"></ion-icon>
            Pases activos ({{ activePasses.length }})
          </h3>
          <ion-list inset>
            <ion-item v-for="p in activePasses" :key="p.id">
              <ion-icon slot="start" :icon="icons.person"></ion-icon>
              <ion-label>
                <h3>{{ p.technician_name || `#${p.technician}` }}</h3>
                <p>{{ p.workspace_name || `#${p.workspace}` }} · Expira: {{ formatExpiry(p.expires_at) }}</p>
              </ion-label>
              <ion-badge :color="p.is_valid ? 'success' : 'warning'" slot="end">
                {{ p.is_valid ? 'ACTIVO' : 'EXPIRADO' }}
              </ion-badge>
              <ion-button
                slot="end"
                fill="outline"
                color="danger"
                size="small"
                :disabled="revokingId === p.id"
                @click="confirmRevoke(p)"
              >
                <ion-spinner v-if="revokingId === p.id" name="crescent"></ion-spinner>
                <template v-else>
                  <ion-icon :icon="icons.close"></ion-icon>
                  Revocar
                </template>
              </ion-button>
            </ion-item>
          </ion-list>
        </div>

        <p v-else class="no-passes ion-text-center">
          <ion-icon :icon="icons.checkmark"></ion-icon>
          No hay pases activos para este ticket.
        </p>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import {
  IonPage, IonHeader, IonToolbar, IonTitle, IonContent,
  IonButtons, IonButton, IonIcon, IonItem, IonLabel, IonNote,
  IonSelect, IonSelectOption, IonSpinner, IonTextarea, IonBadge, IonList,
  alertController, toastController, modalController
} from '@ionic/vue'
import API from '@utils/api/api'

const props = defineProps({
  ticket: {
    type: Object,
    required: true
  }
})

const icons = inject('icons', {})

const technicians = ref([])
const workspaces = ref([])
const passes = ref([])
const loading = ref(true)
const passesLoading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const revokingId = ref(null)

const technicianId = ref(null)
const workspaceId = ref(props.ticket?.workspace ?? null)
const durationHours = ref(4)
const reason = ref('')

const toList = (res) => Array.isArray(res) ? res : (res?.results || res?.data || [])

const activePasses = computed(() =>
  passes.value.filter(p =>
    (String(p.status || '').toUpperCase() === 'ACTIVE') &&
    (String(p.ticket) === String(props.ticket.id) || String(p.ticket_id) === String(props.ticket.id))
  )
)

const formatExpiry = (iso) => {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

const fetchSupportMembers = async () => {
  const res = await API.get(API.SUPPORT_MEMBERS)
  const members = toList(res).map(m => ({
    id: m.id,
    full_name: m.full_name || m.name || m.username || `User #${m.id}`,
    role: m.role || m.position || m.title || ''
  }))
  const preferred = members.filter(m => /technician|support_agent|technico|tecnico/i.test(m.role || ''))
  technicians.value = preferred.length ? preferred : members
}

const fetchWorkspaces = async () => {
  const res = await API.get(API.WORKSPACE)
  workspaces.value = toList(res)
}

const fetchPasses = async () => {
  passesLoading.value = true
  try {
    const res = await API.get(API.DIAGNOSTIC_PASSES)
    passes.value = toList(res)
  } catch (err) {
    console.error('Error fetching diagnostic passes:', err)
  } finally {
    passesLoading.value = false
  }
}

const init = async () => {
  loading.value = true
  loadError.value = ''
  try {
    await Promise.all([fetchSupportMembers(), fetchWorkspaces()])
    if (props.ticket?.id != null) fetchPasses()
  } catch (err) {
    console.error('Error initializing diagnostic pass modal:', err)
    loadError.value = 'No se pudieron cargar los datos necesarios.'
  } finally {
    loading.value = false
  }
}

const showToast = async (message, color = 'success') => {
  const toast = await toastController.create({
    message,
    duration: 3000,
    color,
    position: 'top'
  })
  await toast.present()
}

const confirmGrant = async () => {
  const alert = await alertController.create({
    header: 'Confirmar pase diagnóstico',
    message: `¿Deseas emitir un pase de diagnóstico de ${durationHours.value} horas para el workspace seleccionado?`,
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: 'Emitir',
        role: 'confirm',
        handler: () => { grantPass() }
      }
    ]
  })
  await alert.present()
}

const grantPass = async () => {
  submitting.value = true
  try {
    const payload = {
      technician_id: technicianId.value,
      workspace_id: workspaceId.value,
      duration_hours: Number(durationHours.value)
    }
    if ((reason.value || '').trim()) payload.reason = reason.value.trim()

    await API.post(API.GRANT_DIAGNOSTIC_PASS(props.ticket.id), payload)
    await showToast('Pase diagnóstico emitido exitosamente.')
    modalController.dismiss({ granted: true })
  } catch (err) {
    console.error('Error granting diagnostic pass:', err)
    await showToast(err.message || 'Error al emitir el pase diagnóstico.', 'danger')
  } finally {
    submitting.value = false
  }
}

const confirmRevoke = async (pass) => {
  const alert = await alertController.create({
    header: 'Revocar pase',
    message: `¿Estás seguro de que deseas revocar el pase de ${pass.technician_name || 'este técnico'}?`,
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: 'Revocar',
        role: 'confirm',
        handler: () => { revokePass(pass) }
      }
    ]
  })
  await alert.present()
}

const revokePass = async (pass) => {
  revokingId.value = pass.id
  try {
    await API.post(API.REVOKE_DIAGNOSTIC_PASS(props.ticket.id), { pass_id: pass.id })
    passes.value = passes.value.filter(p => String(p.id) !== String(pass.id))
    await showToast('Pase revocado exitosamente.')
  } catch (err) {
    console.error('Error revoking diagnostic pass:', err)
    await showToast(err.message || 'Error al revocar el pase.', 'danger')
  } finally {
    revokingId.value = null
  }
}

const closeModal = () => {
  modalController.dismiss()
}

onMounted(() => {
  init()
})
</script>

<style scoped>
.ticket-summary {
  margin-bottom: 12px;
}

.warning-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  background: var(--ion-color-warning-tint, #fff6e6);
  margin-bottom: 12px;
  white-space: normal;
}

.error-container {
  margin-top: 40px;
}

.error-container ion-icon {
  font-size: 64px;
  opacity: 0.5;
}

.divider {
  height: 0;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  margin: 16px 0;
}

.passes-section {
  margin-top: 4px;
}

.passes-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  color: #111827;
  margin-bottom: 8px;
}

.no-passes {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #6b7280;
  font-size: 0.9rem;
  margin-top: 12px;
}
</style>