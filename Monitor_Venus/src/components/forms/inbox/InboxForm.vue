<template>
  <div class="inbox-form">
    <div class="header-actions">
      <!-- Signed-in badge -->
      <div v-if="isLoggedIn" class="account-bar">
        <ion-icon :icon="icons.personCircle || icons.person" class="account-icon" />
        <div class="account-text">
          <div class="label">Signed in as</div>
          <div class="value">
            {{ sessionUserLabel }}
            <span v-if="userRole" class="user-role"> • {{ userRole }}</span>
          </div>
        </div>
      </div>

  <ion-searchbar v-model="search" placeholder="Search (sender, subject, text)" class="search" />
  <ion-button v-if="!isMobile" size="small" fill="outline" @click="clearSearch" :disabled="!search">Clear</ion-button>
      <ion-button v-if="!isMobile" size="small" fill="outline" @click="showUnreadOnly = !showUnreadOnly" :color="showUnreadOnly ? 'primary' : 'medium'">
        <ion-icon :icon="showUnreadOnly ? icons.eye : icons.eyeOff" slot="start" />
  {{ showUnreadOnly ? 'Unread only' : 'All' }}
      </ion-button>
      <ion-button v-if="!isMobile" size="small" fill="solid" @click="refreshMock">
        <ion-icon :icon="icons.refresh" slot="start" />
        Refresh
      </ion-button>
      <!-- Mobile refresh icon only -->
      <ion-button v-if="isMobile" size="small" fill="clear" @click="refreshMock">
        <ion-icon :icon="icons.refresh" />
      </ion-button>
  <ion-badge :color="isConnected ? 'success' : 'medium'" title="WebSocket status">{{ isConnected ? 'Live' : 'Offline' }}</ion-badge>
      <ion-spinner v-if="loading" name="dots" />
    </div>
    <div v-if="loadError" class="error-line">{{ loadError }}</div>
    
    <!-- Mobile: show list OR reading pane -->
    <div v-if="isMobile" class="mobile-container">
      <!-- Message list (hidden when reading) -->
      <div v-if="!showMobileReading" class="message-list mobile-list" :class="{ 'empty': filteredMessages.length === 0 }">
        <template v-if="filteredMessages.length">
          <div v-for="msg in filteredMessages" :key="msg.id" :class="['message-item',{selected:msg.id===selectedId,unread:msg.unread}]" @click="selectMessage(msg.id)">
            <div class="message-main">
              <div class="from-subject">
                <span class="from">{{ msg.from }}</span>
                <div class="subject">
                  <span>{{ msg.subject }}</span>
                  <ion-badge class="prio" :color="priorityColor(msg.priority)">{{ msg.priority }}</ion-badge>
                </div>
              </div>
              <div class="meta-row">
                <span class="date">{{ formatDate(msg.date) }}</span>
                <span v-if="msg.unread" class="dot" title="Unread"></span>
              </div>
            </div>
            <div class="snippet">{{ msg.organization || msg.snippet }}</div>
          </div>
        </template>
        <div v-else class="empty-state">
          <ion-icon :icon="icons.inbox" class="empty-icon" />
          <p>No messages match your search.</p>
        </div>
      </div>
      
      <!-- Mobile reading pane (full screen) -->
      <div v-if="showMobileReading && selectedMessage" class="reading-pane mobile-reading">
        <div class="mobile-header">
          <ion-button fill="clear" @click="backToList">
            <ion-icon :icon="icons.arrowBack || icons.chevronBack" slot="icon-only" />
          </ion-button>
          <span class="mobile-title">Message</span>
        </div>
        <div class="reading-content">
          <div class="reading-header">
            <h2 class="reading-subject">{{ selectedMessage.subject }}</h2>
            <div class="reading-actions">
              <ion-badge v-if="selectedMessage.unread" color="primary">Unread</ion-badge>
              <ion-button v-if="isSupportManager" id="assign-trigger-mobile" size="small" fill="outline" @click="openAssignPopover($event)" :disabled="membersLoading || assigning">
                <ion-icon :icon="icons.personAdd || icons.person" slot="icon-only" />
              </ion-button>
              <ion-spinner v-if="isSupportManager && (membersLoading || assigning)" name="dots" />
              <!-- Priority change button -->
              <ion-button v-if="isSupportManager" id="priority-trigger-mobile" size="small" fill="outline" @click="openPriorityPopover($event)" :disabled="!selectedMessage || updatingPriority">
                <ion-icon :icon="icons.flag || icons.alert" slot="icon-only" />
              </ion-button>
              <ion-spinner v-if="isSupportManager && updatingPriority" name="dots" />
              <!-- Popover dropdown for member selection -->
              <ion-popover v-if="isSupportManager" :is-open="assignPopoverOpen" :event="assignPopoverEvent" @didDismiss="assignPopoverOpen=false">
                <ion-content>
                  <ion-list>
                    <ion-item v-if="membersLoading">
                      <ion-spinner name="dots" />
                      <ion-label class="ml-2">Loading members...</ion-label>
                    </ion-item>
                    <ion-item v-for="m in members" :key="m.id" button @click="assigneeId = m.id; assignPopoverOpen=false;">
                      <ion-label>
                        {{ m.name }}<span v-if="m.role" class="role-pill"> • {{ m.role }}</span>
                      </ion-label>
                    </ion-item>
                    <ion-item v-if="!membersLoading && members.length===0">
                      <ion-label>No members found</ion-label>
                    </ion-item>
                  </ion-list>
                </ion-content>
              </ion-popover>
              <!-- Popover for priority selection -->
              <ion-popover v-if="isSupportManager" :is-open="priorityPopoverOpen" :event="priorityPopoverEvent" @didDismiss="priorityPopoverOpen=false">
                <ion-content>
                  <ion-list>
                    <ion-item button @click="setTicketPriority('low')">
                      <ion-label>Low</ion-label>
                    </ion-item>
                    <ion-item button @click="setTicketPriority('medium')">
                      <ion-label>Medium</ion-label>
                    </ion-item>
                    <ion-item button @click="setTicketPriority('high')">
                      <ion-label>High</ion-label>
                    </ion-item>
                    <ion-item button @click="setTicketPriority('urgent')">
                      <ion-label>Urgent</ion-label>
                    </ion-item>
                  </ion-list>
                </ion-content>
              </ion-popover>
            </div>
          </div>
          <div class="reading-meta">
            <span class="from">From: <strong>{{ selectedMessage.from }}</strong></span>
            <span v-if="selectedMessage.email" class="email">Email: <strong>{{ selectedMessage.email }}</strong></span>
            <span class="org">Organization: <strong>{{ selectedMessage.organization }}</strong></span>
            <span class="prio">Priority: <ion-badge :color="priorityColor(selectedMessage.priority)">{{ selectedMessage.priority }}</ion-badge></span>
            <span class="date">{{ formatDate(selectedMessage.date) }}</span>
          </div>
          <div v-if="assigneeId" class="assigned-line">Assigned: <strong>{{ resolveAssigneeName(assigneeId) }}</strong></div>
          <div class="assign-feedback">
            <span v-if="membersError" class="error-line">{{ membersError }}</span>
            <span v-if="assignError" class="error-line">{{ assignError }}</span>
            <span v-if="assignSuccess" class="success-line">{{ assignSuccess }}</span>
            <span v-if="priorityError" class="error-line">{{ priorityError }}</span>
            <span v-if="prioritySuccess" class="success-line">{{ prioritySuccess }}</span>
          </div>
          <div class="detail-grid">
            <div v-if="selectedMessage.category"><label>Category</label><span>{{ selectedMessage.category }}</span></div>
            <div v-if="selectedMessage.infrastructure_category"><label>Infrastructure</label><span>{{ selectedMessage.infrastructure_category }}</span></div>
            <div v-if="selectedMessage.machine_type"><label>Machine</label><span>{{ selectedMessage.machine_type }}</span></div>
            <div v-if="selectedMessage.electric_machine_subtype"><label>Electric</label><span>{{ selectedMessage.electric_machine_subtype }}</span></div>
            <div v-if="selectedMessage.mechanical_machine_subtype"><label>Mechanical</label><span>{{ selectedMessage.mechanical_machine_subtype }}</span></div>
          </div>
          <pre class="reading-body">{{ selectedMessage.body }}</pre>
          <!-- Attachments section -->
          <div class="attachments" v-if="attachmentsLoading || attachmentsError || attachments.length">
            <div class="attachments-title">
              <ion-icon :icon="icons.attach || icons.document" class="attach-icon" />
              <span>Attachments</span>
            </div>
            <div v-if="attachmentsLoading" class="attachments-loading">
              <ion-spinner name="dots" />
              <span>Loading attachments...</span>
            </div>
            <div v-else-if="attachmentsError" class="error-line">{{ attachmentsError }}</div>
            <ul v-else class="attachments-list">
              <li v-for="att in attachments" :key="att.id">
                <a :href="att.url" target="_blank" rel="noopener" :download="att.name">{{ att.name }}</a>
              </li>
            </ul>
          </div>
          
          <!-- Conversation button (only for assigned user) -->
          <div v-if="isAssignedToCurrentUser" class="conversation-button-container">
            <ion-button @click="goToConversation">
              <ion-icon :icon="icons.chatbubbles || icons.chatbox" slot="start" />
              View Conversation
            </ion-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Desktop: split view (list + reading pane side by side) -->
    <div v-else class="split-container">
      <div class="message-list" :class="{ 'empty': filteredMessages.length === 0 }">
        <template v-if="filteredMessages.length">
          <div v-for="msg in filteredMessages" :key="msg.id" :class="['message-item',{selected:msg.id===selectedId,unread:msg.unread}]" @click="selectMessage(msg.id)">
            <div class="message-main">
              <div class="from-subject">
                <span class="from">{{ msg.from }}</span>
                <div class="subject">
                  <span>{{ msg.subject }}</span>
                  <ion-badge class="prio" :color="priorityColor(msg.priority)">{{ msg.priority }}</ion-badge>
                </div>
              </div>
              <div class="meta-row">
                <span class="date">{{ formatDate(msg.date) }}</span>
                <span v-if="msg.unread" class="dot" title="Unread"></span>
              </div>
            </div>
            <div class="snippet">{{ msg.organization || msg.snippet }}</div>
          </div>
        </template>
        <div v-else class="empty-state">
          <ion-icon :icon="icons.inbox" class="empty-icon" />
          <p>No messages match your search.</p>
        </div>
      </div>
      
      <!-- Desktop reading pane -->
      <div class="reading-pane">
        <div v-if="!selectedMessage" class="no-selection">
          <ion-icon :icon="icons.mailOpen || icons.mail" class="placeholder-icon" />
          <p>Select a message to read</p>
        </div>
        <div v-else class="reading-content">
          <div class="reading-header">
            <h2 class="reading-subject">{{ selectedMessage.subject }}</h2>
            <div class="reading-actions">
              <ion-badge v-if="selectedMessage.unread" color="primary">Unread</ion-badge>
              <!-- Mark as read button removed - now automatic when ticket is selected -->
              <ion-button v-if="isSupportManager" id="assign-trigger" size="small" fill="outline" @click="openAssignPopover($event)" :disabled="membersLoading || assigning">
                <ion-icon :icon="icons.personAdd || icons.person" slot="start" />
                <span v-if="assigneeId">Change assigned</span>
                <span v-else>Assign to</span>
              </ion-button>
              <ion-spinner v-if="isSupportManager && (membersLoading || assigning)" name="dots" />
              <!-- Priority change button -->
              <ion-button v-if="isSupportManager" id="priority-trigger" size="small" fill="outline" @click="openPriorityPopover($event)" :disabled="!selectedMessage || updatingPriority">
                <ion-icon :icon="icons.flag || icons.alert" slot="start" />
                Change priority
              </ion-button>
              <ion-spinner v-if="isSupportManager && updatingPriority" name="dots" />
              <!-- Popover dropdown for member selection -->
              <ion-popover v-if="isSupportManager" :is-open="assignPopoverOpen" :event="assignPopoverEvent" @didDismiss="assignPopoverOpen=false">
                <ion-content>
                  <ion-list>
                    <ion-item v-if="membersLoading">
                      <ion-spinner name="dots" />
                      <ion-label class="ml-2">Loading members...</ion-label>
                    </ion-item>
                    <ion-item v-for="m in members" :key="m.id" button @click="assigneeId = m.id; assignPopoverOpen=false;">
                      <ion-label>
                        {{ m.name }}<span v-if="m.role" class="role-pill"> • {{ m.role }}</span>
                      </ion-label>
                    </ion-item>
                    <ion-item v-if="!membersLoading && members.length===0">
                      <ion-label>No members found</ion-label>
                    </ion-item>
                  </ion-list>
                </ion-content>
              </ion-popover>
              <!-- Popover for priority selection -->
              <ion-popover v-if="isSupportManager" :is-open="priorityPopoverOpen" :event="priorityPopoverEvent" @didDismiss="priorityPopoverOpen=false">
                <ion-content>
                  <ion-list>
                    <ion-item button @click="setTicketPriority('low')">
                      <ion-label>Low</ion-label>
                    </ion-item>
                    <ion-item button @click="setTicketPriority('medium')">
                      <ion-label>Medium</ion-label>
                    </ion-item>
                    <ion-item button @click="setTicketPriority('high')">
                      <ion-label>High</ion-label>
                    </ion-item>
                    <ion-item button @click="setTicketPriority('urgent')">
                      <ion-label>Urgent</ion-label>
                    </ion-item>
                  </ion-list>
                </ion-content>
              </ion-popover>
            </div>
          </div>
          <div class="reading-meta">
            <span class="from">From: <strong>{{ selectedMessage.from }}</strong></span>
            <span v-if="selectedMessage.email" class="email">Email: <strong>{{ selectedMessage.email }}</strong></span>
            <span class="org">Organization: <strong>{{ selectedMessage.organization }}</strong></span>
            <span class="prio">Priority: <ion-badge :color="priorityColor(selectedMessage.priority)">{{ selectedMessage.priority }}</ion-badge></span>
            <span class="date">{{ formatDate(selectedMessage.date) }}</span>
          </div>
          <div v-if="assigneeId" class="assigned-line">Assigned: <strong>{{ resolveAssigneeName(assigneeId) }}</strong></div>
          <div class="assign-feedback">
            <span v-if="membersError" class="error-line">{{ membersError }}</span>
            <span v-if="assignError" class="error-line">{{ assignError }}</span>
            <span v-if="assignSuccess" class="success-line">{{ assignSuccess }}</span>
            <span v-if="priorityError" class="error-line">{{ priorityError }}</span>
            <span v-if="prioritySuccess" class="success-line">{{ prioritySuccess }}</span>
          </div>
          <div class="detail-grid">
            <div v-if="selectedMessage.category"><label>Category</label><span>{{ selectedMessage.category }}</span></div>
            <div v-if="selectedMessage.infrastructure_category"><label>Infrastructure</label><span>{{ selectedMessage.infrastructure_category }}</span></div>
            <div v-if="selectedMessage.machine_type"><label>Machine</label><span>{{ selectedMessage.machine_type }}</span></div>
            <div v-if="selectedMessage.electric_machine_subtype"><label>Electric</label><span>{{ selectedMessage.electric_machine_subtype }}</span></div>
            <div v-if="selectedMessage.mechanical_machine_subtype"><label>Mechanical</label><span>{{ selectedMessage.mechanical_machine_subtype }}</span></div>
          </div>
          <pre class="reading-body">{{ selectedMessage.body }}</pre>
          <!-- Attachments section -->
          <div class="attachments" v-if="attachmentsLoading || attachmentsError || attachments.length">
            <div class="attachments-title">
              <ion-icon :icon="icons.attach || icons.document" class="attach-icon" />
              <span>Attachments</span>
            </div>
            <div v-if="attachmentsLoading" class="attachments-loading">
              <ion-spinner name="dots" />
              <span>Loading attachments...</span>
            </div>
            <div v-else-if="attachmentsError" class="error-line">{{ attachmentsError }}</div>
            <ul v-else class="attachments-list">
              <li v-for="att in attachments" :key="att.id">
                <a :href="att.url" target="_blank" rel="noopener" :download="att.name">{{ att.name }}</a>
              </li>
            </ul>
          </div>
          
          <!-- Conversation button (only for assigned user) -->
          <div v-if="isAssignedToCurrentUser" class="conversation-button-container">
            <ion-button @click="goToConversation">
              <ion-icon :icon="icons.chatbubbles || icons.chatbox" slot="start" />
              View Conversation
            </ion-button>
          </div>
        </div>
      </div>
    </div>
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
// ------------------ UI popovers (assignment & priority) ------------------
// Using IonPopover for inline dropdown selection
const assignPopoverOpen = ref(false);
const assignPopoverEvent = ref(null);
function openAssignPopover(ev){ ensureMembers(); assignPopoverEvent.value = ev; assignPopoverOpen.value = true; }

// Priority change popover state and update flags
const priorityPopoverOpen = ref(false);
const priorityPopoverEvent = ref(null);
const updatingPriority = ref(false);
const priorityError = ref('');
const prioritySuccess = ref('');
function openPriorityPopover(ev){ priorityPopoverEvent.value = ev; priorityPopoverOpen.value = true; }

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
    unread: true, // local state placeholder
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
    messages.value = list.map(mapTicketToMessage).sort((a,b) => b.date - a.date);
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
function ensureMembers(){
  if(members.value.length === 0 && !membersLoading.value){ fetchSupportMembers(); }
}

function resolveAssigneeName(id){
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
  return base
    .filter(m => {
      if (showUnreadOnly.value && !m.unread) return false;
      if (!term) return true;
      return (
        (m.from || '').toLowerCase().includes(term) ||
        (m.subject || '').toLowerCase().includes(term) ||
        (m.snippet || '').toLowerCase().includes(term) ||
        (m.body || '').toLowerCase().includes(term) ||
        (m.priority || '').toLowerCase().includes(term)
      );
    })
    .sort((a,b) => b.date - a.date);
});

const selectedMessage = computed(() => messages.value.find(m => m.id === selectedId.value) || null);

// ------------------ Date formatting ------------------
function formatDate(d){ if(!d) return ''; const diffMs=Date.now()-d.getTime(); const diffM=Math.floor(diffMs/60000); const diffH=Math.floor(diffMs/3600_000); if(diffM<1) return 'Just now'; if(diffH<1) return `${diffM} min ago`; if(diffH<24) return `${diffH} h ago`; if(diffH<48) return 'Yesterday'; return d.toLocaleDateString('en-US',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}); }
// ------------------ Selection & UI actions ------------------
/** Select a message, mark read via API, load attachments */
async function selectMessage(id){
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
function clearSearch(){ search.value=''; }
function refreshMock(){ fetchTickets(); }
function priorityColor(p){ const v=(p||'').toLowerCase(); if(v==='high'||v==='urgent') return 'danger'; if(v==='medium') return 'warning'; return 'medium'; }

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
async function setTicketPriority(level){
  if (!isSupportManager.value) { priorityError.value = 'Not allowed'; return; }
  if (!selectedId.value) return;
  const allowed = ['low','medium','high','urgent'];
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
function toAbsoluteUrl(path){
  if (!path) return '';
  if (/^https?:\/\//i.test(String(path))) return String(path);
  try { return new URL(String(path), API.API_BASE_URL).toString(); } catch { return String(path); }
}
function mapAttachmentItem(item){
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
async function fetchAttachments(ticketId){
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
.inbox-form { display: flex; flex-direction: column; gap: 16px; }
.header-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.search { flex: 1 1 280px; }
.split-container { display: grid; grid-template-columns: 360px 1fr; gap: 22px; min-height: calc(70vh); }
.message-list { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 8px 0; display: flex; flex-direction: column; overflow-y: auto; max-height: calc(70vh); text-align: left; }
.message-item { padding: 10px 14px 8px; cursor: pointer; border-bottom: 1px solid #f1f5f9; position: relative; display: flex; flex-direction: column; gap: 4px; text-align: left; align-items: flex-start; }
.message-item:last-child { border-bottom: none; }
.message-item:hover { background: #f8fafc; }
.message-item.selected { background: #eef6ff; }
.message-item.unread .subject { font-weight: 600; }
.message-main { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; width: 100%; }
.from-subject { display: flex; flex-direction: column; gap: 2px; min-width: 0; width: 100%; max-width: 100%; }
.from { font-size: 0.75rem; color: #555; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
.subject { 
  font-size: 0.95rem; 
  color: #111; 
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis; 
  display: flex; 
  align-items: center; 
  gap: 8px;
  max-width: 100%;
}
.subject > span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
.meta-row { display: flex; align-items: center; gap: 6px; }
.date { font-size: 0.7rem; color: #888; }
.dot { width: 8px; height: 8px; background: var(--ion-color-primary); border-radius: 50%; }
.snippet { font-size: 0.85rem; color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-actions { position: absolute; top: 6px; right: 6px; opacity: 0; transition: opacity .2s; }
.message-item:hover .item-actions { opacity: 1; }
.message-item .subject .prio { margin-left: 8px; text-transform: capitalize; font-size: 0.9rem; }
/* Style ion-badge priority in list for better readability */
ion-badge.prio { --padding-start: 6px; --padding-end: 6px; --border-radius: 12px; font-size: 0.78rem; line-height: 1; display: inline-flex; align-items: center; }
/* Emphasize sender email in list */
.from { font-size: 0.9rem; font-weight: 500; }
.message-list.empty { align-items: center; justify-content: center; }
.empty-state { text-align: center; padding: 40px 20px; color: #6b7280; }
.empty-icon { font-size: 64px; color: #d1d5db; margin-bottom: 10px; }
.reading-pane { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 20px 24px; display: flex; flex-direction: column; overflow-y: auto; max-height: calc(70vh); }
.no-selection { margin: auto; text-align: center; color: #6b7280; }
.placeholder-icon { font-size: 70px; color: #d1d5db; margin-bottom: 18px; }
.reading-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.reading-subject { margin: 0; font-size: 1.2rem; font-weight: 600; line-height: 1.3; }
.reading-actions { display: flex; align-items: center; gap: 10px; }
.reading-meta { margin-top: 8px; display: flex; gap: 20px; font-size: 0.8rem; color: #555; flex-wrap: wrap; align-items: center; }
.reading-meta .from strong { font-weight: 600; }
.reading-meta .email strong { font-weight: 600; }
.reading-body { margin-top: 18px; white-space: pre-wrap; font-size: 0.82rem; line-height: 1.5; font-family: var(--ion-font-family, monospace); background: #f9fafb; padding: 14px 16px; border-radius: 10px; border: 1px solid #e5e7eb; }
/* Make metadata (email, organization and priority) larger in reading pane */
.reading-meta .from, .reading-meta .email, .reading-meta .org, .reading-meta .prio { font-size: 0.95rem; }
.reading-meta .prio { display: inline-flex; align-items: center; gap: 6px; line-height: 1; }
.reading-meta .prio ion-badge { --padding-start: 8px; --padding-end: 8px; --border-radius: 12px; font-size: 0.85rem; line-height: 1; }
 .detail-grid { margin-top: 12px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px 16px; }
 .detail-grid label { display:block; font-size: 0.7rem; color: #6b7280; }
 .detail-grid span { font-size: 0.9rem; color: #111827; }
/* Assign-to panel styling */
.assign-inline { display:flex; align-items:center; gap:10px; }
.assignee-select { min-width:210px; }
.role-pill { color:#6b7280; font-size:0.7rem; margin-left:4px; }
.placeholder-text { color:#64748b; }
.assign-feedback { margin-top:6px; display:flex; gap:12px; flex-wrap:wrap; }
.assignee-select .modal-selector-button { 
  padding:4px 14px; 
  border:1px solid var(--ion-color-medium,#6b7280); 
  background:#ffffff; 
  font-size:0.75rem; 
  min-height:32px; 
  display:inline-flex; 
  align-items:center; 
  gap:8px; 
  border-radius:6px; 
  cursor:pointer; 
  transition: background .15s, border-color .15s, box-shadow .15s; 
}
.assignee-select .modal-selector-button:hover { 
  background: var(--ion-color-light,#f1f5f9); 
  border-color: var(--ion-color-primary,#3b82f6); 
}
.assignee-select .modal-selector-button:active { 
  background:#e2e8f0; 
}
.assignee-select .modal-selector-button.disabled { 
  opacity:.55; cursor:not-allowed; 
}
.assignee-select .dropdown-icon { font-size:14px; margin-left:2px; color:#64748b; }
.assign-icon { font-size:16px; color: var(--ion-color-primary,#3b82f6); }
.assignee-select .modal-selector-button span { 
  white-space:nowrap; 
  overflow:hidden; 
  text-overflow:ellipsis; 
  max-width:160px; 
}
.assignee-select .modal-selector-button.assigned { 
  border-color: var(--ion-color-primary,#3b82f6); 
  box-shadow: 0 0 0 1px rgba(59,130,246,0.2); 
}
.assign-display.assigned span { font-weight:600; }
.success-line { color: var(--ion-color-success, #10b981); font-size: 0.8rem; }
.assigned-line { margin-top: 6px; font-size: 0.85rem; color: #374151; }
/* Attachments */
.attachments { margin-top: 14px; }
.attachments-title { display: flex; align-items: center; gap: 8px; font-weight: 700; color: #111827; margin-bottom: 6px; }
.attach-icon { font-size: 18px; color: var(--ion-color-medium,#6b7280); }
.attachments-loading { display:flex; align-items:center; gap:8px; color:#6b7280; font-size:0.9rem; }
.attachments-list { list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-direction: column; gap: 6px; }
.attachments-list a { color: var(--ion-color-primary,#3b82f6); text-decoration: none; }
.attachments-list a:hover { text-decoration: underline; }

/* Conversation button */
.conversation-button-container {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.conversation-button-container ion-button {
  --background: var(--ion-color-primary, #3b82f6);
  --background-hover: #2563eb;
  --color: white;
  font-weight: 600;
  font-size: 0.875rem;
  --padding-start: 12px;
  --padding-end: 16px;
  text-align: center;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: auto;
  min-width: fit-content;
}

.conversation-button-container ion-button ion-icon {
  margin-right: 6px;
}

@media (max-width: 1100px){ .split-container{ grid-template-columns:320px 1fr; } }
@media (max-width: 900px){ .split-container{ grid-template-columns:1fr; } .message-list{ max-height:none; } .reading-pane{ max-height:none; margin-top:8px; } }
@media (max-width: 600px){ .header-actions{ flex-direction:column; align-items:stretch; } .search{ flex:1 1 auto; width:100%; } }
 .error-line { color: var(--ion-color-danger, #ef4444); font-size: 0.85rem; }
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

.mobile-reading .reading-content {
  flex: 1;
  overflow-y: auto;
}

.mobile-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.mobile-reading .reading-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Mobile: hide item actions on list items */
@media (max-width: 768px) {
  .message-item .item-actions {
    display: none;
  }
}
</style>

