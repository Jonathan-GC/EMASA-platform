<template>

  <div class="page-heading">Submit your report here:</div>

      <ion-card>
        <ion-card-content>

          <!-- Signed-in badge (no input field) -->
          <div v-if="isLoggedIn" class="account-bar">
            <ion-icon :icon="personCircleOutline" class="account-icon" />
            <div class="account-text">
              <div class="label">Signed in as</div>
              <div class="value">{{ sessionUserLabel }}</div>
            </div>
          </div>

          <form @submit.prevent="handleSubmit" novalidate>
            <ion-list>

              <!-- Guest-only fields (moved up) -->
              <template v-if="!isLoggedIn">
                <ion-item class="custom" lines="none">
                  <ion-icon :icon="personOutline" slot="start" class="item-icon" />
                  <ion-input
                    class="custom"
                    fill="solid"
                    v-model="form.guest_name"
                    label="Guest Name *"
                    label-placement="floating"
                    type="text"
                    :aria-invalid="!!errors.guest_name"
                    aria-describedby="guest_name-error"
                    @ion-blur="onBlur('guest_name')"
                    placeholder="John Doe"
                  />
                </ion-item>
                <div class="field-error">
                  <ion-note v-if="errors.guest_name && (touched.guest_name || submitAttempted)" id="guest_name-error" color="danger">
                    {{ errors.guest_name }}
                  </ion-note>
                </div>

                <ion-item class="custom" lines="none">
                  <ion-icon :icon="mailOutline" slot="start" class="item-icon" />
                  <ion-input
                    class="custom"
                    fill="solid"
                    v-model="form.guest_email"
                    label="Guest Email *"
                    label-placement="floating"
                    type="email"
                    inputmode="email"
                    autocapitalize="off"
                    autocomplete="email"
                    :aria-invalid="!!errors.guest_email"
                    aria-describedby="guest_email-error"
                    @ion-blur="onBlur('guest_email')"
                    placeholder="guest@example.com"
                  />
                </ion-item>
                <div class="field-error">
                  <ion-note v-if="errors.guest_email && (touched.guest_email || submitAttempted)" id="guest_email-error" color="danger">
                    {{ errors.guest_email }}
                  </ion-note>
                </div>
              </template>

              <div class="divider large-divider"></div>

              <!-- Title -->
              <ion-item class="custom" lines="none">
                <ion-icon :icon="documentTextOutline" slot="start" class="item-icon" />
                <ion-input
                  class="custom"
                  fill="solid"
                  v-model="form.title"
                  label="Title *"
                  label-placement="floating"
                  :maxlength="TITLE_MAX"
                  type="text"
                  inputmode="text"
                  :aria-invalid="!!errors.title"
                  aria-describedby="title-error"
                  @ion-blur="onBlur('title')"
                  placeholder="Short summary of the issue"
                />
              </ion-item>
              <div class="field-error">
                <ion-note v-if="errors.title && (touched.title || submitAttempted)" id="title-error" color="danger">
                  {{ errors.title }}
                </ion-note>
              </div>

              <!-- Description -->
              <ion-item class="custom" lines="none">
                <ion-icon :icon="createOutline" slot="start" class="item-icon" />
                <ion-textarea
                  class="custom"
                  fill="solid"
                  v-model="form.description"
                  label="Description *"
                  label-placement="floating"
                  auto-grow
                  :rows="5"
                  :maxlength="DESC_MAX"
                  :aria-invalid="!!errors.description"
                  aria-describedby="description-error"
                  @ion-blur="onBlur('description')"
                  placeholder="Please describe the problem in detail"
                />
              </ion-item>
              <div class="field-error">
                <ion-note v-if="errors.description && (touched.description || submitAttempted)" id="description-error" color="danger">
                  {{ errors.description }}
                </ion-note>
              </div>

              <div class="divider"></div>

              <!-- Attachment (logged-in only) -->
              <template v-if="isLoggedIn">
                <ion-item class="custom" lines="none">
                  <ion-icon :icon="attachOutline" slot="start" class="item-icon" />
                  <div class="file-field">
                    <div class="file-header">Attachment (optional)</div>


                    <div class="file-row">
                      <input
                        ref="fileInputRef"
                        type="file"
                        class="hidden"
                        :accept="accepts"
                        @change="handleFileChange"
                        aria-label="Upload attachment"
                      />
                      <ion-button fill="outline" size="small" type="button" @click="triggerFilePicker" :disabled="isUploading">
                        Choose file
                      </ion-button>
                      <ion-button
                        v-if="selectedFile"
                        fill="clear"
                        size="small"
                        color="medium"
                        type="button"
                        @click="removeFile"
                        :disabled="isUploading"
                      >
                        Remove
                      </ion-button>
                    </div>

                    <div class="divider small-divider" aria-hidden="true"></div>

                    <div v-if="selectedFile" class="file-chip">
                      <ion-icon :icon="documentAttachOutline" class="chip-icon" />
                      <span class="chip-text">{{ selectedFile.name }}</span>
                      <span class="chip-size">({{ prettyBytes(selectedFile.size) }})</span>
                      <ion-button fill="clear" size="small" color="danger" class="chip-remove" @click="removeFile" :disabled="isUploading">
                        ✕
                      </ion-button>
                    </div>

                    <ion-note color="medium" class="hint">
                      Allowed: PNG, JPG, JPEG, PDF, DOC, DOCX, TXT. Max size: {{ prettyBytes(MAX_FILE_SIZE) }}.
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
            <div class="actions">
              <ion-button type="button" fill="outline" color="medium" @click="resetForm" :disabled="isBusy">Clear</ion-button>
              <div class="button-divider" aria-hidden="true"></div>
              <ion-button type="submit" :disabled="isBusy || !isValid">
                <ion-spinner v-if="isBusy" slot="start" />
                Submit
              </ion-button>
            </div>
          </form>
        </ion-card-content>
      </ion-card>

      <!-- UX helpers -->
      <ion-loading :is-open="isBusy" message="Submitting..." />
      <ion-toast
        :is-open="toast.open"
        :message="toast.message"
        :color="toast.color"
        :duration="2600"
        @didDismiss="toast.open = false"
      />

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
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import {
  IonPage, IonToolbar, IonTitle, IonContent, IonCard, IonCardHeader, IonCardContent,
  IonList, IonItem, IonInput, IonTextarea, IonNote, IonButton, IonSpinner, IonToast, IonLoading, IonIcon,
} from '@ionic/vue'
import { personOutline, personCircleOutline, mailOutline, attachOutline, documentAttachOutline, createOutline, documentTextOutline } from 'ionicons/icons'
import API from '@/utils/api/api'

// ------------------ Model & Constraints ------------------
type SupportTicketPayload = {
  title: string
  description: string
  guest_name?: string
  guest_email?: string
  user?: string | number
}

const TITLE_MAX = 100
const DESC_MAX = 1000

const form = reactive<SupportTicketPayload>({
  title: '',
  description: '',
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
        try { localStorage.setItem('sb_user_id', String(uid)) } catch {}
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
  title: null, description: null, guest_name: null, guest_email: null, user: null,
})

// touched map and submitAttempted flag: only show errors after blur or submit
const touched = reactive<Record<string, boolean>>({ title: false, description: false, guest_name: false, guest_email: false, user: false })
const submitAttempted = ref(false)

function onBlur(field: keyof SupportTicketPayload) {
  touched[String(field)] = true
  validateField(field)
}

function validateField(field: keyof SupportTicketPayload) {
  const val = (form[field] ?? '').toString().trim()
  switch (field) {
    case 'title':
      errors.title = val.length < 3 ? 'Title must be at least 3 characters.' : null
      break
    case 'description':
      errors.description = val.length < 10 ? 'Description must be at least 10 characters.' : null
      break
    case 'guest_name':
      errors.guest_name = !isLoggedIn.value && val.length < 2 ? 'Guest name must be at least 2 characters.' : null
      break
    case 'guest_email': {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      errors.guest_email = !isLoggedIn.value && !emailRegex.test(val) ? 'Please enter a valid email address.' : null
      break
    }
  }
}
function validateAll(): boolean {
  ;(['title', 'description'] as (keyof SupportTicketPayload)[]).forEach(validateField)
  if (!isLoggedIn.value) {
    ;(['guest_name', 'guest_email'] as (keyof SupportTicketPayload)[]).forEach(validateField)
  } else {
    errors.guest_name = null
    errors.guest_email = null
  }
  const baseOk = !!form.title?.trim() && !!form.description?.trim() && !errors.title && !errors.description
  const guestOk = isLoggedIn.value ? true : !!form.guest_name?.trim() && !!form.guest_email?.trim() && !errors.guest_name && !errors.guest_email
  return baseOk && guestOk
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
  const k = 1024, sizes = ['B','KB','MB','GB','TB']
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
  const allowed = ['image/png','image/jpg','image/jpeg','application/pdf','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document','text/plain']
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
const RAW_TICKET = (API as any).SUPPORT_TICKET || 'support/ticket'
const TICKET_ENDPOINT = RAW_TICKET
const ALT_TICKET = RAW_TICKET.endsWith('/') ? RAW_TICKET.slice(0, -1) : `${RAW_TICKET}/`

// Attachment (FormData)
const RAW_ATTACHMENT = (API as any).ATTACMEENT_CREATE || 'support/ticket/attachment'
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
      if (key in errors) { ;(errors as any)[key] = String(first) }
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
  // Clear values
  form.title = ''
  form.description = ''
  form.guest_name = ''
  form.guest_email = ''

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
    for (const k of Object.keys(errors)) { ;(errors as any)[k] = null }
  } catch (_) { /* ignore */ }
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

    // Build ticket payload
    const payload: SupportTicketPayload = {
      title: form.title.trim(),
      description: form.description.trim(),
    }
    if (isLoggedIn.value && sessionUserId.value != null) {
      payload.user = sessionUserId.value // IMPORTANT: backend expects "user"
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
  font-size: 1.2rem; /* increased per user request */
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
  color: var(--ion-color-warning, #ff8c00); /* make icons orange for guest/title/description/file */
}

/* File preview chip */
.file-field { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.file-header { font-size: 0.95rem; font-weight: 600; color: var(--ion-color-medium-contrast, #222); margin-bottom: 2px; }
.file-row { display: flex; gap: 8px; align-items: center; }
.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--ion-color-light, #f3f4f6);
  border-radius: 9999px;
  padding: 4px 8px;
  margin-top: 6px;
}
.chip-icon { font-size: 16px; color: var(--ion-color-warning, #ff8c00); }
.chip-text { font-weight: 600; }
.chip-size { color: var(--ion-color-medium); font-size: 12px; }
.chip-remove { margin-left: 2px; }

.actions {
  display: flex;
  gap: 12px;
  justify-content: center; /* center buttons */
  margin-top: 8px;
}

/* Make textarea use same tokens as input.custom */
:deep(ion-item.custom) ion-textarea.custom {
  --placeholder-color: #858585;
  --border-color: #cccccc;
  --highlight-color-focused: #000000;
}

/* Heading and divider used by SupportForm layout tweaks */
.page-heading{ text-align:left; font-size:1.6rem; font-weight:800; margin:8px 0 }
.divider{ height:0; border-top:1px solid rgba(0,0,0,0.08); margin:6px 0 }
.large-divider{ margin:16px 0 } /* extra spacing between guest fields and Title */
.small-divider{ height:0; border-top:1px solid rgba(0,0,0,0.06); margin:6px 0 }
.button-divider{ width:1px; background:var(--ion-color-medium); opacity:0.12; margin:0 12px; align-self:center; height:22px }
</style>