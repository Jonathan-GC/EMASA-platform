<template>


  <ion-card>
    <ion-card-content>

      <!-- Signed-in badge (no input field) -->
      <div v-if="isLoggedIn" class="account-bar">
        <ion-icon :icon="personCircleOutline" class="account-icon" />
        <div class="account-text">
          <div class="label">Conectado como</div>
          <div class="value">{{ sessionUserLabel }}</div>
        </div>
      </div>

      <form @submit.prevent="handleSubmit" novalidate>
        <ion-list>

          <!-- Title -->
          <ion-item class="custom" lines="none">
            <ion-label position="stacked" class="!mb-2">Asunto *</ion-label>
            <ion-input class="custom" fill="solid" v-model="form.title" :maxlength="TITLE_MAX" type="text"
              inputmode="text" :aria-invalid="!!errors.title" aria-describedby="title-error" @ion-blur="onBlur('title')"
              placeholder="Resumen breve del problema" />
          </ion-item>

          <div class="field-error">
            <ion-note v-if="errors.title && (touched.title || submitAttempted)" id="title-error" color="danger">
              {{ errors.title }}
            </ion-note>
          </div>

          <div v-if="!isLoggedIn" class="divider large-divider"></div>

          <!-- Guest-only fields (moved up) -->
          <template v-if="!isLoggedIn">
            <ion-item class="custom" lines="none">
              <ion-label position="stacked" class="!mb-2">Nombre *</ion-label>
              <ion-input class="custom" fill="solid" v-model="form.guest_name"
                type="text" :aria-invalid="!!errors.guest_name"
                aria-describedby="guest_name-error" @ion-blur="onBlur('guest_name')" placeholder="Fulano Detal" />
            </ion-item>
            <div class="field-error">
              <ion-note v-if="errors.guest_name && (touched.guest_name || submitAttempted)" id="guest_name-error"
                color="danger">
                {{ errors.guest_name }}
              </ion-note>
            </div>

            <ion-item class="custom" lines="none">
              <ion-label position="stacked" class="!mb-2">Correo electrónico *</ion-label>
              <ion-input class="custom" fill="solid" v-model="form.guest_email" 
                type="email" inputmode="email" autocapitalize="off" autocomplete="email"
                :aria-invalid="!!errors.guest_email" aria-describedby="guest_email-error"
                @ion-blur="onBlur('guest_email')" placeholder="ejemplo@mail.com" />
            </ion-item>
            <div class="field-error">
              <ion-note v-if="errors.guest_email && (touched.guest_email || submitAttempted)" id="guest_email-error"
                color="danger">
                {{ errors.guest_email }}
              </ion-note>
            </div>
          </template>

          <div class="divider large-divider"></div>

          <div class="field-error">
          </div>

          <!-- Ticket types: chained selectors -->
          <ion-list>
            <ion-item class="custom">
              <ion-label position="stacked" class=" !mb-2">Categoría *</ion-label>
              <ModalSelector class="custom" v-model="ticketSelection.category" :options="categoryOptions"
                :value-field="'code'" :display-field="'name'" :search-fields="['name']" title="Seleccionar categoría"
                placeholder=" -" search-placeholder="Buscar Categoría..." :disabled="loadingTypes">
                <template #option="{ option }">
                  <ion-label>{{ option.name }}</ion-label>
                </template>
              </ModalSelector>
            </ion-item>
            <div class="field-error">
              <ion-note v-if="errors.category && (touched.category || submitAttempted)" id="category-error"
                color="danger">
                {{ errors.category }}
              </ion-note>
            </div>

            <ion-item v-if="ticketSelection.category === 'infrastructure'" class="custom">
              <ion-label position="stacked" class="!mb-2">Infrastructura</ion-label>
              <ModalSelector class="custom" v-model="ticketSelection.infrastructure" :options="infraOptions"
                :value-field="'code'" :display-field="'name'" :search-fields="['name']"
                title="Seleccionar infrastructura" placeholder=" -" search-placeholder="Buscar infrastructura..."
                :disabled="loadingTypes">
                <template #option="{ option }">
                  <ion-label>{{ option.name }}</ion-label>
                </template>
              </ModalSelector>
            </ion-item>
            <div class="field-error">
              <ion-note v-if="errors.infrastructure_category && (touched.infrastructure_category || submitAttempted)"
                id="infrastructure_category-error" color="danger">
                {{ errors.infrastructure_category }}
              </ion-note>
            </div>

            <ion-item v-if="ticketSelection.infrastructure === 'machines'" class="custom">
              <ion-label position="stacked" class="!mb-2">Tipo de máquina</ion-label>
              <ModalSelector class="custom" v-model="ticketSelection.machine_type" :options="machineTypeOptions"
                :value-field="'code'" :display-field="'name'" :search-fields="['name']"
                title="Seleccionar tipo de máquina" placeholder=" -" search-placeholder="Buscar tipo de máquina..."
                :disabled="loadingTypes">
                <template #option="{ option }">
                  <ion-label>{{ option.name }}</ion-label>
                </template>
              </ModalSelector>
            </ion-item>
            <div class="field-error">
              <ion-note v-if="errors.machine_type && (touched.machine_type || submitAttempted)" id="machine_type-error"
                color="danger">
                {{ errors.machine_type }}
              </ion-note>
            </div>

            <ion-item v-if="ticketSelection.machine_type === 'electric'" class="custom">
              <ion-label position="stacked" class="!mb-2">Subtipo de máquina eléctrica</ion-label>
              <ModalSelector class="custom" v-model="ticketSelection.electric_subtype" :options="electricSubtypeOptions"
                :value-field="'code'" :display-field="'name'" :search-fields="['name']"
                title="Seleccionar subtipo de máquina eléctrica" placeholder=" -" search-placeholder="Buscar subtipo..."
                :disabled="loadingTypes">
                <template #option="{ option }">
                  <ion-label>{{ option.name }}</ion-label>
                </template>
              </ModalSelector>
            </ion-item>
            <div class="field-error">
              <ion-note v-if="errors.electric_machine_subtype && (touched.electric_machine_subtype || submitAttempted)"
                id="electric_machine_subtype-error" color="danger">
                {{ errors.electric_machine_subtype }}
              </ion-note>
            </div>

            <ion-item v-if="ticketSelection.machine_type === 'mechanical'" class="custom">
              <ion-label position="stacked" class="!mb-2">Subtipo de máquina mecánica</ion-label>
              <ModalSelector class="custom" v-model="ticketSelection.mechanical_subtype"
                :options="mechanicalSubtypeOptions" :value-field="'code'" :display-field="'name'"
                :search-fields="['name']" title="Seleccionar subtipo de máquina mecánica" placeholder=" -"
                search-placeholder="Buscar subtipo..." :disabled="loadingTypes">
                <template #option="{ option }">
                  <ion-label>{{ option.name }}</ion-label>
                </template>
              </ModalSelector>
            </ion-item>
            <div class="field-error">
              <ion-note
                v-if="errors.mechanical_machine_subtype && (touched.mechanical_machine_subtype || submitAttempted)"
                id="mechanical_machine_subtype-error" color="danger">
                {{ errors.mechanical_machine_subtype }}
              </ion-note>
            </div>
          </ion-list>


          <!-- Description -->
          <!-- Organization (optional) -->
          <ion-item class="custom" lines="none">
            <ion-label position="stacked" class=" !mb-2">Organización</ion-label>
            <ion-input class="custom" fill="solid" v-model="form.organization" type="text" inputmode="text"
              :aria-invalid="!!errors.organization" aria-describedby="organization-error"
              @ion-blur="onBlur('organization')" placeholder="MTR SAS" />
          </ion-item>
          <div class="field-error">
            <ion-note v-if="errors.organization && (touched.organization || submitAttempted)" id="organization-error"
              color="danger">
              {{ errors.organization }}
            </ion-note>
          </div>
          <ion-item class="custom" lines="none">
            <ion-label position="stacked" class=" !mb-2">Descripción *</ion-label>
            <ion-textarea class="custom" fill="solid" v-model="form.description" auto-grow :rows="5"
              :maxlength="DESC_MAX" :aria-invalid="!!errors.description" aria-describedby="description-error"
              @ion-blur="onBlur('description')"
              placeholder="Por favor describa el problema con el mayor detalle posible." />
          </ion-item>
          <div class="field-error">
            <ion-note v-if="errors.description && (touched.description || submitAttempted)" id="description-error"
              color="danger">
              {{ errors.description }}
            </ion-note>
          </div>

          <div class="divider"></div>

          <!-- Attachment (logged-in only) -->
          <template v-if="isLoggedIn">
            <ion-item class="custom" lines="none">
              <div class="file-field">
                <div class="file-header">Attachment (optional)</div>


                <div class="file-row">
                  <input ref="fileInputRef" type="file" class="hidden" :accept="accepts" @change="handleFileChange"
                    aria-label="Upload attachment" />
                  <ion-button fill="outline" size="small" type="button" @click="triggerFilePicker"
                    :disabled="isUploading" shape="round">
                     <ion-icon :icon="attachOutline" slot="start"/>
                    Adjuntar archivo
                  </ion-button>
                  <ion-button v-if="selectedFile" fill="clear" size="small" color="medium" type="button"
                    @click="removeFile" :disabled="isUploading">
                    Eliminar
                  </ion-button>
                </div>

                <div class="divider small-divider" aria-hidden="true"></div>

                <div v-if="selectedFile" class="file-chip">
                  <ion-icon :icon="documentAttachOutline" class="chip-icon" />
                  <span class="chip-text">{{ selectedFile.name }}</span>
                  <span class="chip-size">({{ prettyBytes(selectedFile.size) }})</span>
                  <ion-button fill="clear" size="small" color="danger" class="chip-remove" @click="removeFile"
                    :disabled="isUploading">
                    ✕
                  </ion-button>
                </div>

                <ion-note color="medium" class="hint">
                  Permitidos: PNG, JPG, JPEG, PDF, DOC, DOCX, TXT | Tamaño máximo: {{ prettyBytes(MAX_FILE_SIZE) }}.
                </ion-note>
                <ion-note v-if="fileError" color="danger" class="hint">
                  {{ fileError }}
                </ion-note>
              </div>
            </ion-item>
          </template>
        </ion-list>

        <div class="divider"></div>

        <!-- Actions -->
        <div class="actions ion-text-end">
          <ion-button type="button" fill="outline" color="medium" @click="resetForm" :disabled="isBusy" shape="round">
            <ion-icon :icon="syncOutline" slot="start" />
            Limpiar
          </ion-button>
          
          <ion-button type="submit" :disabled="isBusy || !isValid" shape="round">
            <ion-spinner v-if="isBusy" slot="start" />
            <ion-icon :icon="paperPlaneOutline" slot="start" />
            Enviar
          </ion-button>
        </div>
      </form>
    </ion-card-content>
  </ion-card>

  <!-- UX helpers -->
  <ion-loading :is-open="isBusy" message="Submitting..." />
  <ion-toast :is-open="toast.open" :message="toast.message" :color="toast.color" :duration="2600"
    @didDismiss="toast.open = false" />

</template>

<script setup lang="ts">
// ---------------------------------------------------------------------------
// Support Form (refined UI/UX + inline API + attachment upload)
// - Shows "Signed in as <name>" instead of a User input when logged in.
// - Guest flow remains, with icons, helpers and counters.
// - Step 1: POST support/ticket (JSON) with "user" when logged in.
// - Step 2: POST ATTACMEENT_CREATE (FormData) with { file, ticket }.
// - Extracts ticketId even if the response is an array.
// ---------------------------------------------------------------------------
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import {
  IonPage, IonToolbar, IonTitle, IonContent, IonCard, IonCardHeader, IonCardContent,
  IonList, IonItem, IonInput, IonTextarea, IonNote, IonButton, IonSpinner, IonToast, IonLoading, IonIcon,
} from '@ionic/vue'
import { personOutline, personCircleOutline, mailOutline, attachOutline, documentAttachOutline, createOutline, documentTextOutline, listOutline, syncOutline, paperPlaneOutline } from 'ionicons/icons'
import API from '@/utils/api/api'
import ModalSelector from '@/components/ui/ModalSelector.vue'

// Summary of recent changes made to this file:
// - Fetch ticket type lists from API (GET_TYPES) and store in `typesData`.
// - Add chained selectors (ModalSelector) for category -> infrastructure -> machine type -> subtype.
// - Map API objects to option arrays and reset dependent selections when parent changes.
// - Include the selected type fields in the ticket POST payload and reset them on form reset.
// - Apply `class="custom"` to selectors so they match other input styles.

// ------------------ Model & Constraints ------------------
type SupportTicketPayload = {
  title: string
  description: string
  organization?: string | null
  guest_name?: string
  guest_email?: string
  user_id?: string | number
  category?: string | null
  infrastructure_category?: string | null
  machine_type?: string | null
  electric_machine_subtype?: string | null
  mechanical_machine_subtype?: string | null
}

const TITLE_MAX = 100
const DESC_MAX = 1000

const form = reactive<SupportTicketPayload>({
  title: '',
  description: '',
  organization: '',
  guest_name: '',
  guest_email: '',
})

// ------------------ Auth (token + user name/email) ------------------
function base64UrlDecode(input: string): string {
  input = input.replace(/-/g, '+').replace(/_/g, '/')
  const pad = input.length % 4
  if (pad) input += '='.repeat(4 - pad)
  try { return atob(input) } catch { return '' }
}
function decodeJwtPayload(token: string): any | null {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  const json = base64UrlDecode(parts[1])
  try { return JSON.parse(json) } catch { return null }
}
function extractUserId(claims: any): string | number | null {
  if (!claims || typeof claims !== 'object') return null
  return claims.user_id ?? claims.userId ?? claims.sub ?? null
}

const authToken = ref<string | null>(null)
const isLoggedIn = computed(() => !!authToken.value)
const sessionUserId = ref<string | number | null>(null)
const sessionUserLabel = ref('Authenticated user')

async function loadSessionContext() {
  try {
    authToken.value = API?.getValidToken?.() || null
    if (!authToken.value) {
      const cached = localStorage.getItem('sb_user_id')
      if (cached) sessionUserId.value = isNaN(+cached) ? cached : +cached
    }
    if (authToken.value) {
      const claims = decodeJwtPayload(authToken.value)
      const uid = extractUserId(claims)
      if (uid != null) {
        sessionUserId.value = uid
        try { localStorage.setItem('sb_user_id', String(uid)) } catch { }
      }
      // Try to extract a friendly display name from the JWT claims immediately
      // Prefer common claim names (name, full_name, given_name, preferred_username, username, email)
      try {
        const nameFromClaims = claims?.name || claims?.full_name || claims?.given_name || claims?.preferred_username || claims?.username || claims?.email || null
        if (nameFromClaims) {
          sessionUserLabel.value = String(nameFromClaims)
        }
      } catch (e) {
        // ignore parsing errors, keep default label
      }
      // Pretty label from API.me() if available
      if (typeof (API as any).me === 'function') {
        try {
          const profile = await (API as any).me()
          const name = profile?.name || profile?.full_name || profile?.username || null
          const email = profile?.email || null
          sessionUserLabel.value = name ? (email ? `${name} <${email}>` : name) : (email || 'Authenticated user')
        } catch { /* ignore */ }
      }
    }
  } catch {
    authToken.value = null
  }
}

function handleStorage(e: StorageEvent) {
  if (e.key?.toLowerCase().includes('token')) loadSessionContext()
}

onMounted(() => {
  loadSessionContext()
  window.addEventListener('storage', handleStorage)
})
onBeforeUnmount(() => {
  window.removeEventListener('storage', handleStorage)
})

// ------------------ Validation ------------------
const toast = reactive<{ open: boolean; message: string; color: 'success' | 'danger' | 'warning' | 'medium' }>({
  open: false, message: '', color: 'success',
})
const isSubmitting = ref(false)
const isUploading = ref(false)
const isBusy = computed(() => isSubmitting.value || isUploading.value)

const errors = reactive<Record<keyof Required<SupportTicketPayload>, string | null>>({
  title: null,
  description: null,
  organization: null,
  guest_name: null,
  guest_email: null,
  user_id: null,
  category: null,
  infrastructure_category: null,
  machine_type: null,
  electric_machine_subtype: null,
  mechanical_machine_subtype: null,
})

// touched map and submitAttempted flag: only show errors after blur or submit
const touched = reactive<Record<string, boolean>>({ title: false, description: false, organization: false, guest_name: false, guest_email: false, user_id: null, category: false, infrastructure_category: false, machine_type: false, electric_machine_subtype: false, mechanical_machine_subtype: false })
const submitAttempted = ref(false)

function onBlur(field: keyof SupportTicketPayload) {
  touched[String(field)] = true
  validateField(field)
}

function validateField(field: keyof SupportTicketPayload) {
  // handle form fields
  if (field === 'title' || field === 'description' || field === 'guest_name' || field === 'guest_email') {
    const val = (form[field] ?? '').toString().trim()
    switch (field) {
      case 'title':
        errors.title = val.length < 5 ? 'El asunto debe tener al menos 5 caracteres.' : null
        break
      case 'description':
        errors.description = val.length < 10 ? 'La descripción debe tener al menos 10 caracteres.' : null
        break
      case 'guest_name':
        errors.guest_name = !isLoggedIn.value && val.length < 2 ? 'El nombre del invitado debe tener al menos 2 caracteres.' : null
        break
      case 'guest_email': {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        errors.guest_email = !isLoggedIn.value && !emailRegex.test(val) ? 'Por favor, introduce una dirección de correo electrónico válida.' : null
        break
      }
    }
    return
  }

  // organization: optional text, enforce maximum length only
  if (field === 'organization') {
    const val = (form.organization ?? '').toString().trim()
    errors.organization = val && val.length > 100 ? 'Organization must be 100 characters or less.' : null
    return
  }

  // handle selection fields (ticketSelection)
  if (field === 'category') {
    errors.category = !ticketSelection.category ? 'Please select a category.' : null
    return
  }
  if (field === 'infrastructure_category') {
    // required only when category === 'infrastructure'
    errors.infrastructure_category = ticketSelection.category === 'infrastructure' && !ticketSelection.infrastructure ? 'Please select an infrastructure.' : null
    return
  }
  if (field === 'machine_type') {
    // required only when infrastructure === 'machines'
    errors.machine_type = ticketSelection.infrastructure === 'machines' && !ticketSelection.machine_type ? 'Please select a machine type.' : null
    return
  }
  if (field === 'electric_machine_subtype') {
    errors.electric_machine_subtype = ticketSelection.machine_type === 'electric' && !ticketSelection.electric_subtype ? 'Please select an electric subtype.' : null
    return
  }
  if (field === 'mechanical_machine_subtype') {
    errors.mechanical_machine_subtype = ticketSelection.machine_type === 'mechanical' && !ticketSelection.mechanical_subtype ? 'Please select a mechanical subtype.' : null
    return
  }
}
function validateAll(): boolean {
  ; (['title', 'description'] as (keyof SupportTicketPayload)[]).forEach(validateField)
    ; (['organization'] as (keyof SupportTicketPayload)[]).forEach(validateField)
  if (!isLoggedIn.value) {
    ; (['guest_name', 'guest_email'] as (keyof SupportTicketPayload)[]).forEach(validateField)
  } else {
    errors.guest_name = null
    errors.guest_email = null
  }
  // validate selection fields
  ; (['category', 'infrastructure_category', 'machine_type', 'electric_machine_subtype', 'mechanical_machine_subtype'] as (keyof SupportTicketPayload)[]).forEach(validateField)
  const baseOk = !!form.title?.trim() && !!form.description?.trim() && !errors.title && !errors.description
  const guestOk = isLoggedIn.value ? true : !!form.guest_name?.trim() && !!form.guest_email?.trim() && !errors.guest_name && !errors.guest_email
  const selectionOk = !errors.category && !errors.infrastructure_category && !errors.machine_type && !errors.electric_machine_subtype && !errors.mechanical_machine_subtype
  return baseOk && guestOk && selectionOk
}
const isValid = computed(() => validateAll())

// ------------------ File handling ------------------
const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const fileError = ref<string | null>(null)

const accepts = '.png,.jpg,.jpeg,.pdf,.doc,.docx,.txt'
const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5 MB

function prettyBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}
function triggerFilePicker() { fileInputRef.value?.click() }
function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  fileError.value = null
  if (!file) { selectedFile.value = null; return }
  if (file.size > MAX_FILE_SIZE) {
    fileError.value = `File is too large. Max ${prettyBytes(MAX_FILE_SIZE)}.`
    input.value = ''; selectedFile.value = null; return
  }
  const allowed = ['image/png', 'image/jpg', 'image/jpeg', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!allowed.includes(file.type) && !accepts.includes(ext)) {
    fileError.value = 'Unsupported file type.'
    input.value = ''; selectedFile.value = null; return
  }
  selectedFile.value = file
}
function removeFile() {
  selectedFile.value = null
  fileError.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

// ------------------ API endpoints ------------------
// Ticket (JSON)
const RAW_TICKET = (API as any).SUPPORT_TICKET || 'support/ticket/'
const TICKET_ENDPOINT = RAW_TICKET
const ALT_TICKET = RAW_TICKET.endsWith('/') ? RAW_TICKET.slice(0, -1) : `${RAW_TICKET}/`

// Attachment (FormData)
const RAW_ATTACHMENT = (API as any).ATTACMEENT_CREATE || 'support/ticket/attachment/'
const ATTACHMENT_ENDPOINT = RAW_ATTACHMENT
const ALT_ATTACHMENT = RAW_ATTACHMENT.endsWith('/') ? RAW_ATTACHMENT.slice(0, -1) : `${RAW_ATTACHMENT}/`

function logServerError(err: any) {
  const status = err?.response?.status || err?.status
  const data = err?.response?.data || err?.data
  console.error('[Support] Server error status:', status)
  console.error('[Support] Server error body:', data)
}
function mapServerErrors(err: any) {
  const serverErrors = err?.response?.data?.errors || err?.data?.errors || err?.errors || null
  if (serverErrors && typeof serverErrors === 'object') {
    for (const [key, value] of Object.entries(serverErrors)) {
      const first = Array.isArray(value) ? value[0] : value
      if (key in errors) { ; (errors as any)[key] = String(first) }
    }
  }
}

// POST JSON (ticket) with alt URL fallback
async function postJson(endpoint: string, alt: string, body: any) {
  try { return await API.post(endpoint, body) }
  catch (e1: any) {
    console.warn('[Support] POST failed on', endpoint, e1?.message || e1)
    try { return await API.post(alt, body) }
    catch (e2: any) { console.warn('[Support] POST failed on', alt, e2?.message || e2); throw e2 }
  }
}

// POST FormData (attachment)
async function postFormData(endpoint: string, alt: string, fd: FormData) {
  try { return await API.post(endpoint, fd) }
  catch (e1: any) {
    console.warn('[Support] FormData POST failed on', endpoint, e1?.message || e1)
    try { return await API.post(alt, fd) }
    catch (e2: any) { console.warn('[Support] FormData POST failed on', alt, e2?.message || e2); throw e2 }
  }
}

// Extract ticketId from array/object/data
function getTicketId(res: any): number | string | null {
  if (!res) return null
  if (Array.isArray(res)) return res[0]?.id ?? null
  if (Array.isArray(res?.data)) return res.data[0]?.id ?? null
  if (res?.data?.id != null) return res.data.id
  if (res?.id != null) return res.id
  return null
}

async function uploadAttachment(ticketId: string | number, file: File) {
  const fd = new FormData()
  fd.append('file', file)              // backend expects "file"
  fd.append('ticket', String(ticketId))// backend expects "ticket"
  const res = await postFormData(ATTACHMENT_ENDPOINT, ALT_ATTACHMENT, fd)
  return res
}

function resetForm() {
  // Prevent watchers from treating our programmatic clear as user interaction
  isResetting.value = true
  // Clear values
  form.title = ''
  form.description = ''
  form.organization = ''
  form.guest_name = ''
  form.guest_email = ''
  // Clear ticket selections
  try { ticketSelection.category = null; ticketSelection.infrastructure = null; ticketSelection.machine_type = null; ticketSelection.electric_subtype = null; ticketSelection.mechanical_subtype = null } catch (_) { }

  // Clear file and file errors
  removeFile()
  fileError.value = null

  // Reset validation visibility state so no errors are shown after clearing
  submitAttempted.value = false
  // reset touched flags
  try {
    for (const k of Object.keys(touched)) { (touched as any)[k] = false }
  } catch (_) { /* ignore */ }
  // clear error messages (they won't be visible while touched/submitAttempted are false,
  // but clear them to avoid stale state)
  try {
    for (const k of Object.keys(errors)) { ; (errors as any)[k] = null }
  } catch (_) { /* ignore */ }
  // allow watchers to operate normally again
  isResetting.value = false
}

// ------------------ Submit flow ------------------
async function handleSubmit() {
  // mark submit attempt so errors become visible
  submitAttempted.value = true
  if (!isValid.value) {
    toast.open = true
    toast.message = 'Please review the form fields.'
    toast.color = 'warning'
    return
  }

  try {
    isSubmitting.value = true

    // Build ticket payload — only include optional fields when they have values.
    // Some backends error when receiving explicit `null` for fields they don't expect,
    // so omit undefined/null fields entirely.
    const payload: Record<string, any> = {
      title: form.title.trim(),
      description: form.description.trim(),
    }

    // optional organization
    if (form.organization && String(form.organization).trim()) payload.organization = String(form.organization).trim()
    // selections: only add if present
    if (ticketSelection.category) payload.category = ticketSelection.category
    if (ticketSelection.infrastructure) payload.infrastructure_category = ticketSelection.infrastructure
    if (ticketSelection.machine_type) payload.machine_type = ticketSelection.machine_type
    if (ticketSelection.electric_subtype) payload.electric_machine_subtype = ticketSelection.electric_subtype
    if (ticketSelection.mechanical_subtype) payload.mechanical_machine_subtype = ticketSelection.mechanical_subtype

    if (isLoggedIn.value && sessionUserId.value != null) {
      payload.user_id = sessionUserId.value // IMPORTANT: backend expects "user_id"
    } else if (!isLoggedIn.value) {
      payload.guest_name = form.guest_name?.trim()
      payload.guest_email = form.guest_email?.trim()
    }


    // Step 1: Create ticket
    const resTicket = await postJson(TICKET_ENDPOINT, ALT_TICKET, payload)
    if (resTicket?.error) throw { message: resTicket?.message || 'Failed to create ticket', ...resTicket }

    const ticketId = getTicketId(resTicket)

    if (ticketId == null) {
      toast.open = true
      toast.message = 'Ticket created but could not resolve its ID.'
      toast.color = 'warning'
    } else if (isLoggedIn.value && selectedFile.value) {
      // Step 2: Upload attachment
      isUploading.value = true
      try {
        await uploadAttachment(ticketId, selectedFile.value)
        toast.open = true
        toast.message = 'Ticket created and attachment uploaded.'
        toast.color = 'success'
      } catch (e) {
        console.error('[Support] Attachment upload error:', e)
        logServerError(e)
        toast.open = true
        toast.message = 'Ticket created, but attachment upload failed.'
        toast.color = 'warning'
      } finally {
        isUploading.value = false
      }
    } else {
      toast.open = true
      toast.message = 'Support request created successfully.'
      toast.color = 'success'
    }

    // Reset after success
    resetForm()
  } catch (err: any) {
    console.error('[Support] Ticket creation error:', err)
    logServerError(err)
    mapServerErrors(err)
    toast.open = true
    toast.message = err?.message || 'Something went wrong. Please try again.'
    toast.color = 'danger'
  } finally {
    isSubmitting.value = false
  }
}

// --- Get for spport types ---


onMounted(async () => {
  try {
    const types = await API.get(API.GET_TYPES)
    // store response in a constant usable by the template
    typesData.value = Array.isArray(types) ? types[0] : types || {}
    console.log('GET_TYPES response:', typesData.value)
  } catch (err) {
    console.error('GET_TYPES error:', err)
  }
})

// --- Types / selections for chained selectors ---
const typesData = ref({})
const loadingTypes = ref(false)

const ticketSelection = reactive({
  category: null,
  infrastructure: null,
  machine_type: null,
  electric_subtype: null,
  mechanical_subtype: null,
})

// used to prevent watchers from marking fields as "touched" during programmatic resets
const isResetting = ref(false)

const categoryOptions = computed(() => {
  const cats = typesData.value?.categories || {}
  return Object.entries(cats).map(([code, name]) => ({ code, name }))
})
const infraOptions = computed(() => {
  const cats = typesData.value?.infrastructure_categories || {}
  return Object.entries(cats).map(([code, name]) => ({ code, name }))
})
const machineTypeOptions = computed(() => {
  const types = typesData.value?.machine_types || {}
  return Object.entries(types).map(([code, name]) => ({ code, name }))
})
const electricSubtypeOptions = computed(() => {
  const subs = typesData.value?.electric_machine_subtypes || {}
  return Object.entries(subs).map(([code, name]) => ({ code, name }))
})
const mechanicalSubtypeOptions = computed(() => {
  const subs = typesData.value?.mechanical_machine_subtypes || {}
  return Object.entries(subs).map(([code, name]) => ({ code, name }))
})

// Reset dependent selections when parent changes
watch(() => ticketSelection.category, (v) => {
  if (v !== 'infrastructure') {
    ticketSelection.infrastructure = null
    ticketSelection.machine_type = null
    ticketSelection.electric_subtype = null
    ticketSelection.mechanical_subtype = null
  }
  // mark touched for validation UI unless we're resetting programmatically
  if (!isResetting.value) touched.category = true
})
watch(() => ticketSelection.infrastructure, (v) => {
  if (v !== 'machines') {
    ticketSelection.machine_type = null
    ticketSelection.electric_subtype = null
    ticketSelection.mechanical_subtype = null
  }
  if (!isResetting.value) touched.infrastructure_category = true
})
watch(() => ticketSelection.machine_type, (v) => {
  if (v !== 'electric') ticketSelection.electric_subtype = null
  if (v !== 'mechanical') ticketSelection.mechanical_subtype = null
  if (!isResetting.value) touched.machine_type = true
})
watch(() => ticketSelection.electric_subtype, (v) => { if (!isResetting.value) touched.electric_machine_subtype = true })
watch(() => ticketSelection.mechanical_subtype, (v) => { if (!isResetting.value) touched.mechanical_machine_subtype = true })
</script>

<style scoped>
/* Compact account badge */
.account-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px 12px 4px;
  margin-bottom: 8px;
}

.account-icon {
  font-size: 30px;
  color: var(--ion-color-primary);
}

.account-text .label {
  font-size: 13px;
  color: var(--ion-color-medium);
  line-height: 1.1;
}

.account-text .value {
  font-weight: 700;
  color: var(--ion-color-dark);
  line-height: 1.2;
  font-size: 1.2rem;
  /* increased per user request */
}

/* Row hints and icons */
.row-hint {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0 16px 8px 16px;
}

.item-icon {
  font-size: 20px;
  color: var(--ion-color-warning, #ff8c00);
  /* make icons orange for guest/title/description/file */
}

/* Selector labels (stacked) should match other input label sizing */
.selector-label {
  font-size: 1rem;
  font-weight: 600;
  color: var(--ion-color-dark);
}

/* File preview chip */
.file-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.file-header {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ion-color-medium-contrast, #222);
  margin-bottom: 2px;
}

.file-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--ion-color-light, #f3f4f6);
  border-radius: 9999px;
  padding: 4px 8px;
  margin-top: 6px;
}

.chip-icon {
  font-size: 16px;
  color: var(--ion-color-warning, #ff8c00);
}

.chip-text {
  font-weight: 600;
}

.chip-size {
  color: var(--ion-color-medium);
  font-size: 12px;
}

.chip-remove {
  margin-left: 2px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: right;
  /* center buttons */
  margin-top: 8px;
}

/* Make textarea use same tokens as input.custom */
:deep(ion-item.custom) ion-textarea.custom {
  --placeholder-color: #858585;
  --border-color: #cccccc;
  --highlight-color-focused: #000000;
}

/* Heading and divider used by SupportForm layout tweaks */
.page-heading {
  text-align: left;
  font-size: 1.6rem;
  font-weight: 800;
  margin: 8px 0
}

.divider {
  height: 0;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  margin: 6px 0
}

.large-divider {
  margin: 16px 0
}

/* extra spacing between guest fields and Title */
.small-divider {
  height: 0;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  margin: 6px 0
}

.button-divider {
  width: 1px;
  background: var(--ion-color-medium);
  opacity: 0.12;
  margin: 0 12px;
  align-self: center;
  height: 22px
}
</style>