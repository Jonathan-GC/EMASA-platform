<template>
  <div class="inbox-form">
    <div class="header-actions">
      <!-- Signed-in badge -->
      <div v-if="isLoggedIn" class="account-bar">
        <ion-icon :icon="icons.personCircle || icons.person" class="account-icon" />
        <div class="account-text">
          <div class="label">Conecado como</div>
          <div class="value">
            {{ sessionUserLabel }}
            <span v-if="userRole" class="user-role"> • {{ userRole }}</span>
          </div>
        </div>
      </div>

      <ion-searchbar v-model="search" placeholder="Buscar (remitente, asunto, texto)" class="search custom" />
        <ConnectionStatus :is-connected="isConnected" :reconnect-attempts="reconnectAttempts" />
      <ion-spinner v-if="loading" name="dots" />
    </div>
    <div v-if="loadError" class="error-line">{{ loadError }}</div>

    <!-- Mobile: show list OR reading pane -->
    <div v-if="isMobile" class="mobile-container">
      <!-- Message list (hidden when reading) -->
      <MessageList 
        v-if="!showMobileReading"
        class="mobile-list"
        :filtered-messages="filteredMessages"
        :selected-id="selectedId"
        :format-date="formatDate"
        :priority-color="priorityColor"
        :has-search="!!search"
        :show-unread-only="showUnreadOnly"
        :current-sort-field="sortField"
        :sort-ascending="sortAscending"
        @select="selectMessage"
        @clear-search="clearSearch"
        @toggle-unread="showUnreadOnly = !showUnreadOnly"
        @refresh="refreshMock"
        @sort-by="handleSortBy"
        @toggle-sort-direction="toggleSortDirection"
      />

      <!-- Mobile reading pane (full screen) -->
      <div v-if="showMobileReading && selectedMessage" class="mobile-reading">
        <div class="mobile-header">
          <ion-button fill="clear" @click="backToList">
            <ion-icon :icon="icons.arrowBack || icons.chevronBack" slot="icon-only" />
          </ion-button>
          <span class="mobile-title">Message</span>
        </div>
        <MessageReadingPane
          :selected-message="selectedMessage"
          :is-support-manager="isSupportManager"
          :is-mobile="true"
          :members-loading="membersLoading"
          :assigning="assigning"
          :updating-priority="updatingPriority"
          :assignee-id="assigneeId"
          :members-error="membersError"
          :assign-error="assignError"
          :assign-success="assignSuccess"
          :priority-error="priorityError"
          :priority-success="prioritySuccess"
          :attachments="attachments"
          :attachments-loading="attachmentsLoading"
          :attachments-error="attachmentsError"
          :is-assigned-to-current-user="isAssignedToCurrentUser"
          :format-date="formatDate"
          :priority-color="priorityColor"
          :resolve-assignee-name="resolveAssigneeName"
          @open-assign-popover="openAssignPopover"
          @open-priority-popover="openPriorityPopover"
          @go-to-conversation="goToConversation"
        />
      </div>
    </div>

    <!-- Desktop: split view (list + reading pane side by side) -->
    <div v-else class="split-container">
      <MessageList 
        :filtered-messages="filteredMessages"
        :selected-id="selectedId"
        :format-date="formatDate"
        :priority-color="priorityColor"
        :has-search="!!search"
        :show-unread-only="showUnreadOnly"
        :current-sort-field="sortField"
        :sort-ascending="sortAscending"
        @select="selectMessage"
        @clear-search="clearSearch"
        @toggle-unread="showUnreadOnly = !showUnreadOnly"
        @refresh="refreshMock"
        @sort-by="handleSortBy"
        @toggle-sort-direction="toggleSortDirection"
      />

      <MessageReadingPane
        :selected-message="selectedMessage"
        :is-support-manager="isSupportManager"
        :is-mobile="false"
        :members-loading="membersLoading"
        :assigning="assigning"
        :updating-priority="updatingPriority"
        :assignee-id="assigneeId"
        :members-error="membersError"
        :assign-error="assignError"
        :assign-success="assignSuccess"
        :priority-error="priorityError"
        :priority-success="prioritySuccess"
        :attachments="attachments"
        :attachments-loading="attachmentsLoading"
        :attachments-error="attachmentsError"
        :is-assigned-to-current-user="isAssignedToCurrentUser"
        :format-date="formatDate"
        :priority-color="priorityColor"
        :resolve-assignee-name="resolveAssigneeName"
        @open-assign-popover="openAssignPopover"
        @open-priority-popover="openPriorityPopover"
        @go-to-conversation="goToConversation"
      />
    </div>
    
    <!-- Shared Popovers (used by both mobile and desktop) -->
    <ion-popover v-if="isSupportManager" :is-open="assignPopoverOpen" :event="assignPopoverEvent"
      @didDismiss="assignPopoverOpen = false">
      <ion-content>
        <ion-list>
          <ion-item v-if="membersLoading">
            <ion-spinner name="dots" />
            <ion-label class="ml-2">Cargando miembros...</ion-label>
          </ion-item>
          <ion-item v-for="m in members" :key="m.id" button
            @click="assigneeId = m.id; assignPopoverOpen = false;">
            <ion-label>
              {{ m.name }}<span v-if="m.role" class="role-pill"> • {{ m.role }}</span>
            </ion-label>
          </ion-item>
          <ion-item v-if="!membersLoading && members.length === 0">
            <ion-label>No se encontraron miembros</ion-label>
          </ion-item>
        </ion-list>
      </ion-content>
    </ion-popover>
    
    <ion-popover v-if="isSupportManager" :is-open="priorityPopoverOpen" :event="priorityPopoverEvent"
      @didDismiss="priorityPopoverOpen = false">
      <ion-content>
        <ion-list>
          <ion-item button @click="setTicketPriority('low')">
            <ion-label>Baja</ion-label>
          </ion-item>
          <ion-item button @click="setTicketPriority('medium')">
            <ion-label>Media</ion-label>
          </ion-item>
          <ion-item button @click="setTicketPriority('high')">
            <ion-label>Alta</ion-label>
          </ion-item>
          <ion-item button @click="setTicketPriority('urgent')">
            <ion-label>Urgente</ion-label>
          </ion-item>
        </ion-list>
      </ion-content>
    </ion-popover>
  </div>
</template>

<script setup>
// ---------------------------------------------------------------------------
// InboxForm (Support Inbox)
// - Email-style inbox: list, search bar, reading pane.
// - Integrated with APIs: SUPPORT_TICKET, SUPPORT_MEMBERS, ATTACMEENT_CREATE.
// - Ticket assignment and priority changes (GET/POST/PATCH flows).
// - User info comes embedded in each ticket now (no extra USER calls).
// - Attachments per ticket (GET support/attachment/?ticket_id=<id>) with a clear
//   message when none exist.
// - This reorganization only adds comments/separators for readability.
// ---------------------------------------------------------------------------
import { ref, computed, inject, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import { useNotifications } from '@/composables/useNotifications';
import { useResponsiveView } from '@/composables/useResponsiveView';
import { IonSearchbar, IonButton, IonBadge, IonSpinner, IonIcon, IonLabel, IonPopover, IonList, IonItem, IonContent } from '@ionic/vue';
import API from '@/utils/api/api';
import ConnectionStatus from '@/components/ConnectionStatus.vue';
import MessageList from './MessageList.vue';
import MessageReadingPane from './MessageReadingPane.vue';
// ------------------ UI popovers (assignment & priority) ------------------
// Using IonPopover for inline dropdown selection
const assignPopoverOpen = ref(false);
const assignPopoverEvent = ref(null);
function openAssignPopover(ev) { ensureMembers(); assignPopoverEvent.value = ev; assignPopoverOpen.value = true; }

// Priority change popover state and update flags
const priorityPopoverOpen = ref(false);
const priorityPopoverEvent = ref(null);
const updatingPriority = ref(false);
const priorityError = ref('');
const prioritySuccess = ref('');
function openPriorityPopover(ev) { priorityPopoverEvent.value = ev; priorityPopoverOpen.value = true; }

// ------------------ Injected icons ------------------
const icons = inject('icons', {});

// ------------------ Router ------------------
const router = useRouter();

// ------------------ Responsive ------------------
const { isMobile } = useResponsiveView(768);
const showMobileReading = ref(false);

// ------------------ Base inbox state ------------------
// Reactive list mapped from SUPPORT_TICKET endpoint
const messages = ref([]);
const search = ref('');
const showUnreadOnly = ref(false);
const selectedId = ref(null);
const loading = ref(false);
const loadError = ref('');

// ------------------ Sorting state ------------------
const sortField = ref('date');
const sortAscending = ref(false);

// ------------------ Auth & role ------------------
const auth = useAuthStore();
const currentUserId = computed(() => auth.userId);
const isLoggedIn = computed(() => auth.isAuthenticated);
const sessionUserLabel = ref('Authenticated user');
const userRole = ref('');

// Load session context: display name from auth store
async function loadSessionContext() {
  try {
    if (!auth.isAuthenticated) return;
    const name = auth.username || null;
    sessionUserLabel.value = name || 'Authenticated user';

    // Role will be set after fetching support members
    userRole.value = '';
  } catch {
    sessionUserLabel.value = 'Authenticated user';
    userRole.value = '';
  }
}

// Update user role based on support members list
function updateUserRole() {
  if (!auth.isAuthenticated || !currentUserId.value) {
    userRole.value = '';
    return;
  }

  const currentMember = members.value.find(m => String(m.id) === String(currentUserId.value));
  if (currentMember && currentMember.role) {
    userRole.value = currentMember.role;
  } else {
    // Fallback to generic labels if not found in support members
    if (auth.isSuperUser) {
      userRole.value = 'Superuser';
    } else if (auth.isGlobalUser) {
      userRole.value = 'Global Admin';
    } else {
      userRole.value = 'User';
    }
  }
}

// Determine if the user is a support manager (or admin/global)
// Heuristic: superuser OR admin => manager; OR support member whose role contains 'manager'
const isSupportManager = computed(() => {
  if (auth.isSuperUser || auth.isAdmin) return true;
  // Si miembros cargados tienen rol y coincide con manager
  return members.value.some(m => String(m.id) === String(currentUserId.value || '') &&
    typeof m.role === 'string' && /manager/i.test(m.role));
});

// Check if current user is assigned to the selected ticket
const isAssignedToCurrentUser = computed(() => {
  if (!selectedMessage.value || !currentUserId.value) return false;
  return String(selectedMessage.value.assigned_to) === String(currentUserId.value);
});

// ------------------ User info ------------------
// User info is included in each ticket payload; no remote lookup needed

// ------------------ Attachments ------------------
// Attachments for the selected ticket
const attachments = ref([]); // [{ id, name, url }]
const attachmentsLoading = ref(false);
const attachmentsError = ref('');

// ------------------ Assignment (support members) ------------------
// Assign-to state (inline popover selector)
const members = ref([]); // { id, name }
const membersLoading = ref(false);
const membersError = ref('');
const assigneeId = ref(null);
// Delegate (assign) state
const assigning = ref(false);
const assignError = ref('');
const assignSuccess = ref('');
// prevent POST when we set assignee programmatically
const skipAssignPost = ref(false);

// ------------------ Mapping & helpers ------------------
/** Map raw backend ticket to inbox message item */
function mapTicketToMessage(t) {
  // Prefer human-friendly name for display in both list and reading pane
  // 1) guest_name (if present)
  // 2) if no guest, use embedded user.full_name/email
  // 3) fallback to guest_email
  // 4) '(Unknown)'
  const guestName = (t.guest_name || '').toString().trim();
  const guestEmail = (t.guest_email || '').toString().trim();
  const userObj = t.user && typeof t.user === 'object' ? t.user : null;
  const userFullName = (userObj?.full_name || userObj?.name || userObj?.username || '').toString().trim();
  const userEmail = (userObj?.email || '').toString().trim();
  const fromDisplay = guestName
    || userFullName
    || guestEmail
    || '(Unknown)';

  const created = t.created_at ? new Date(t.created_at) : new Date();
  return {
    id: t.id,
    from: fromDisplay,
    user_id: userObj?.id ?? null,
    email: guestEmail || userEmail || '',
    subject: t.title || '(Untitled)',
    snippet: t.organization || '',
    body: t.description || '',
    date: created,
    unread: !t.is_read, // Based on backend is_read field (false means unread)
    priority: t.priority || 'low',
    category: t.category || '',
    organization: t.organization || '',
    infrastructure_category: t.infrastructure_category || '',
    machine_type: t.machine_type || '',
    electric_machine_subtype: t.electric_machine_subtype || '',
    mechanical_machine_subtype: t.mechanical_machine_subtype || '',
    status: t.status || '',
    created_at: t.created_at,
    updated_at: t.updated_at,
    assigned_to: t.assigned_to ?? null,
  };
}

// ------------------ Ticket loading ------------------
/** Fetch tickets, sort, preselect first, sync assignment & attachments */
async function fetchTickets() {
  loading.value = true;
  loadError.value = '';
  try {
    const res = await API.get(API.SUPPORT_TICKET);
    const list = Array.isArray(res) ? res : (res?.results || []);
    messages.value = list.map(mapTicketToMessage).sort((a, b) => b.date - a.date);
    // Don't auto-select any ticket - user must click to view
    // selectedId.value = messages.value[0]?.id ?? null;
  } catch (err) {
    console.error('Error fetching tickets', err);
    loadError.value = err?.message || 'Could not load tickets.';
    messages.value = [];
    selectedId.value = null;
  } finally {
    loading.value = false;
  }
}

// ------------------ Support members ------------------
/** Load support members for assignment popover */
async function fetchSupportMembers() {
  membersLoading.value = true;
  membersError.value = '';
  try {
    const res = await API.get(API.SUPPORT_MEMBERS);
    const list = Array.isArray(res) ? res : (res?.results || []);
    members.value = list.map((m) => ({ id: m.id, name: m.full_name || m.name || `User #${m.id}`, role: m.role || m.position || m.title }));
    // Update user role after loading members
    updateUserRole();
  } catch (error) {
    console.error('Error fetching support members:', error);
    membersError.value = error?.message || 'Could not load support members.';
  } finally {
    membersLoading.value = false;
  }
}

// ------------------ Assignment utilities ------------------
// Ensure members are fetched prior to opening selector
function ensureMembers() {
  if (members.value.length === 0 && !membersLoading.value) { fetchSupportMembers(); }
}

function resolveAssigneeName(id) {
  const m = members.value.find(mm => mm.id === id);
  return m ? m.name : (id ? `#${id}` : '');
}

// ------------------ Filtering & derived values ------------------
const filteredMessages = computed(() => {
  const term = search.value.trim().toLowerCase();
  // Role-based visibility: support managers see all; others see created-by or assigned-to
  const base = messages.value.filter(m => {
    if (isSupportManager.value) return true;
    const uid = String(currentUserId.value || '');
    return String(m.user_id || '') === uid || String(m.assigned_to || '') === uid;
  });
  
  const filtered = base.filter(m => {
    if (showUnreadOnly.value && !m.unread) return false;
    if (!term) return true;
    return (
      (m.from || '').toLowerCase().includes(term) ||
      (m.subject || '').toLowerCase().includes(term) ||
      (m.snippet || '').toLowerCase().includes(term) ||
      (m.body || '').toLowerCase().includes(term) ||
      (m.priority || '').toLowerCase().includes(term)
    );
  });
  
  // Apply sorting
  return filtered.sort((a, b) => {
    let comparison = 0;
    const field = sortField.value;
    
    switch(field) {
      case 'date':
        comparison = a.date - b.date;
        break;
      case 'from':
        comparison = (a.from || '').localeCompare(b.from || '');
        break;
      case 'organization':
        comparison = (a.organization || '').localeCompare(b.organization || '');
        break;
      case 'priority': {
        const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
        const aPrio = priorityOrder[a.priority?.toLowerCase()] || 0;
        const bPrio = priorityOrder[b.priority?.toLowerCase()] || 0;
        comparison = aPrio - bPrio;
        break;
      }
      case 'subject':
        comparison = (a.subject || '').localeCompare(b.subject || '');
        break;
      case 'status':
        comparison = (a.status || '').localeCompare(b.status || '');
        break;
      default:
        comparison = b.date - a.date;
    }
    
    return sortAscending.value ? comparison : -comparison;
  });
});

const selectedMessage = computed(() => messages.value.find(m => m.id === selectedId.value) || null);

// ------------------ Date formatting ------------------
function formatDate(d) { if (!d) return ''; const diffMs = Date.now() - d.getTime(); const diffM = Math.floor(diffMs / 60000); const diffH = Math.floor(diffMs / 3600_000); if (diffM < 1) return 'Just now'; if (diffH < 1) return `${diffM} min ago`; if (diffH < 24) return `${diffH} h ago`; if (diffH < 48) return 'Yesterday'; return d.toLocaleDateString('en-US', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }); }
// ------------------ Selection & UI actions ------------------
/** Select a message, mark read via API, load attachments */
async function selectMessage(id) {
  selectedId.value = id;
  const m = messages.value.find(m => m.id === id);

  // Mark as read via API if unread
  if (m && m.unread) {
    await markAsRead(id);
  }

  skipAssignPost.value = true;
  assigneeId.value = m?.assigned_to ?? null;
  nextTick(() => { skipAssignPost.value = false; });
  if (assigneeId.value && members.value.length === 0 && !membersLoading.value) {
    fetchSupportMembers();
  }
  // fetch attachments for this ticket
  if (id) fetchAttachments(id);
  // On mobile, show reading pane full screen
  if (isMobile.value) {
    showMobileReading.value = true;
  }
}

/** Mark ticket as read via API */
async function markAsRead(ticketId) {
  try {
    console.log('📧 Marking ticket as read:', ticketId);
    const endpoint = API.INBOX_READ(ticketId);
    await API.post(endpoint);
    console.log('✅ Ticket marked as read');

    // Update local state
    const m = messages.value.find(m => m.id === ticketId);
    if (m) m.unread = false;
  } catch (err) {
    console.error('❌ Error marking ticket as read:', err);
    // Don't show error to user, it's not critical
  }
}

// Go back to list on mobile
function backToList() {
  showMobileReading.value = false;
  selectedId.value = null;
}

// Navigate to conversation view with ticket ID
function goToConversation() {
  if (selectedId.value) {
    router.push({
      path: '/ticket',
      query: { id: selectedId.value }
    });
  }
}

// If initial ticket has an assignee and we don't yet have member data, fetch it to resolve the name
// Unified initialization
onMounted(async () => {
  // Load user context
  await loadSessionContext();
  // Load members first (for role info) then tickets
  await fetchSupportMembers();
  await fetchTickets();
});
// Minor UI handlers
function clearSearch() { search.value = ''; }
function refreshMock() { fetchTickets(); }
function priorityColor(p) { const v = (p || '').toLowerCase(); if (v === 'high' || v === 'urgent') return 'danger'; if (v === 'medium') return 'warning'; return 'medium'; }

// Sorting handlers
function handleSortBy(field) { sortField.value = field; }
function toggleSortDirection() { sortAscending.value = !sortAscending.value; }

// WebSocket notifications: refresh tickets when any notification arrives
const { notifications, isConnected, connectionStatus } = useNotifications();
let refreshTimeout = null;
watch(() => notifications.value[0], () => {
  // Debounce: refresh 700ms after last notification
  if (refreshTimeout) clearTimeout(refreshTimeout);
  refreshTimeout = setTimeout(() => {
    fetchTickets();
  }, 700);
});

// Clear the debounce timer on component unmount
onUnmounted(() => {
  if (refreshTimeout) {
    clearTimeout(refreshTimeout);
    refreshTimeout = null;
  }
});

// ------------------ Watchers (assignment) ------------------
// Watch assigneeId to POST delegation (send only staff id)
watch(assigneeId, async (newId, oldId) => {
  if (!isSupportManager.value) return; // guard: only managers can assign
  if (skipAssignPost.value) return;
  if (!selectedId.value || newId == null) return;
  assignError.value = '';
  assignSuccess.value = '';
  assigning.value = true;
  try {
    await API.post(API.DELEGATE(selectedId.value), { assigned_to_id: newId });
    const msg = messages.value.find(m => m.id === selectedId.value);
    if (msg) msg.assigned_to = newId;
    assignSuccess.value = 'Assignment saved';
    setTimeout(() => { assignSuccess.value = ''; }, 1800);
  } catch (e) {
    console.error('Error delegating ticket:', e);
    assignError.value = e?.message || 'Failed to assign';
    // revert local selection
    skipAssignPost.value = true;
    assigneeId.value = oldId ?? null;
    nextTick(() => { skipAssignPost.value = false; });
  } finally {
    assigning.value = false;
  }
});

// (No remote user lookup needed; user info comes with each ticket)

// ------------------ Priority change ------------------
// Update ticket priority via PATCH support/ticket/{id}/ with { priority }
async function setTicketPriority(level) {
  if (!isSupportManager.value) { priorityError.value = 'Not allowed'; return; }
  if (!selectedId.value) return;
  const allowed = ['low', 'medium', 'high', 'urgent'];
  const target = String(level || '').toLowerCase();
  if (!allowed.includes(target)) { priorityError.value = 'Invalid priority'; return; }
  const msg = messages.value.find(m => m.id === selectedId.value);
  if (msg && (msg.priority || '').toLowerCase() === target) {
    priorityPopoverOpen.value = false; // no-op if same
    return;
  }
  updatingPriority.value = true;
  priorityError.value = '';
  prioritySuccess.value = '';
  try {
    // PATCH the priority
    const endpoint = API.SUPPORT_TICKET + String(selectedId.value) + '/';
    await API.patch(endpoint, { priority: target });

    // Refresh the entire ticket list to ensure all users see the update via WebSocket
    await fetchTickets();

    // Re-select the current ticket after refresh
    selectedId.value = msg?.id ?? null;
    if (selectedId.value) {
      const refreshedMsg = messages.value.find(m => m.id === selectedId.value);
      if (refreshedMsg) {
        skipAssignPost.value = true;
        assigneeId.value = refreshedMsg.assigned_to ?? null;
        await nextTick();
        skipAssignPost.value = false;
      }
    }

    prioritySuccess.value = 'Priority updated';
    setTimeout(() => { prioritySuccess.value = ''; }, 1800);
  } catch (e) {
    console.error('Error updating priority:', e);
    priorityError.value = e?.message || 'Failed to update priority';
  } finally {
    updatingPriority.value = false;
    priorityPopoverOpen.value = false;
  }
}
// ------------------ Attachments: helpers & loading ------------------
// Helper: map attachment response items to display model
function toAbsoluteUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(String(path))) return String(path);
  try { return new URL(String(path), API.API_BASE_URL).toString(); } catch { return String(path); }
}
function mapAttachmentItem(item) {
  const url = item?.file || item?.url || item?.download_url || '';
  const abs = toAbsoluteUrl(url);
  let name = item?.filename || item?.name || '';
  if (!name && abs) {
    try { name = decodeURIComponent(abs.split('/').pop() || 'attachment'); } catch { name = 'attachment'; }
  }
  return {
    id: item?.id ?? name ?? abs,
    name: String(name || 'attachment'),
    url: abs,
  };
}

// Fetch attachments for a ticket id (filtered by ticket_id query param)
async function fetchAttachments(ticketId) {
  if (!ticketId) { attachments.value = []; attachmentsError.value = 'No attachments found here'; return; }
  attachmentsLoading.value = true;
  attachmentsError.value = '';
  attachments.value = [];
  try {
    // Preferred endpoint pattern: support/attachment/?ticket_id=<id>
    const endpoint = `${API.ATTACMEENT_CREATE}?ticket_id=${encodeURIComponent(ticketId)}`;
    const res = await API.get(endpoint);
    let list = Array.isArray(res) ? res : (res?.results || []);
    // Fallback: if objects have ticket or ticket_id property, filter strictly
    list = list.filter(it => {
      const tid = it.ticket_id ?? it.ticket?.id ?? it.ticket;
      return tid == ticketId; // loose equality for number/string
    });
    attachments.value = list.map(mapAttachmentItem).filter(a => !!a.url);
    if (attachments.value.length === 0) {
      attachmentsError.value = 'No attachments found here';
    }
  } catch (err) {
    // Suppress noisy 404 in console per user request; only log non-404 for diagnostics
    const msg = String(err?.message || '').toLowerCase();
    if (!msg.includes('404')) {
      console.error('Error fetching attachments:', err);
    }
    attachmentsError.value = 'No attachments found here';
  } finally {
    attachmentsLoading.value = false;
  }
}
</script>




<style scoped>
.inbox-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.search {
  flex: 1 1 280px;
}

.split-container {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 22px;
  min-height: calc(70vh);
}

.role-pill {
  color: #6b7280;
  font-size: 0.7rem;
  margin-left: 4px;
}

.error-line {
  color: var(--ion-color-danger, #ef4444);
  font-size: 0.85rem;
}

/* Account badge */
.account-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 4px;
  background: var(--ion-color-light, #f5f5f5);
  border-radius: 8px;
  border: 1px solid var(--ion-color-light-shade, #e0e0e0);
}

.account-icon {
  font-size: 26px;
  color: var(--ion-color-primary);
}

.account-text .label {
  font-size: 11px;
  color: var(--ion-color-medium);
  line-height: 1.1;
}

.account-text .value {
  font-weight: 600;
  color: var(--ion-color-dark);
  line-height: 1.2;
  font-size: 0.95rem;
}

.user-role {
  color: var(--ion-color-medium);
  font-size: 0.85rem;
  font-weight: 500;
}

/* Mobile responsive styles */
.mobile-container {
  display: flex;
  flex-direction: column;
  height: calc(70vh);
  position: relative;
}

.mobile-list {
  flex: 1;
  overflow-y: auto;
}

.mobile-reading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #ffffff;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.mobile-header {
  position: sticky;
  top: 0;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 10;
  flex-shrink: 0;
}

.mobile-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

@media (max-width: 1100px) {
  .split-container {
    grid-template-columns: 320px 1fr;
  }
}

@media (max-width: 900px) {
  .split-container {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .search {
    flex: 1 1 auto;
    width: 100%;
  }
}
</style>
