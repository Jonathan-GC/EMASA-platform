<template>
  <div class="conversation-form">
    <!-- Loading state -->
    <div v-if="loading" class="loading-container">
      <ion-spinner name="dots" />
      <p>Loading conversation...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-container">
      <ion-icon :icon="icons.alertCircle" class="error-icon" />
      <p class="error-text">{{ error }}</p>
      <ion-button @click="loadConversation">Retry</ion-button>
    </div>

    <div v-else-if="conversationData" class="conversation-content">
      <!-- Expanded Ticket Header -->
      <div class="ticket-header-compact">
        <div class="header-inner">
          <div class="header-main">
            <div class="title-section">
              <span class="ticket-id">#{{ conversationData.id.toString().substring(0, 8) }}</span>
              <h2>{{ conversationData.title }}</h2>
            </div>
            <div class="header-meta">
              <ion-badge :color="priorityColor(conversationData.priority)">{{ conversationData.priority }}</ion-badge>
              <ion-badge :color="statusColor(conversationData.status)">{{ conversationData.status }}</ion-badge>
            </div>
          </div>
          
          <div class="header-details-grid">
            <div class="detail-item">
              <ion-icon :icon="icons.calendar" />
              <span>Creado: {{ formatDate(conversationData.created_at) }}</span>
            </div>
            <div class="detail-item" v-if="conversationData.category">
              <ion-icon :icon="icons.pricetag" />
              <span>Categoria: {{ conversationData.category }}</span>
            </div>
            <div class="detail-item" v-if="conversationData.organization">
              <ion-icon :icon="icons.business" />
              <span>Org: {{ conversationData.organization }}</span>
            </div>
            <div class="detail-item" v-if="conversationData.user_email || conversationData.guest_email">
              <ion-icon :icon="icons.mail" />
              <span>{{ conversationData.user_email || conversationData.guest_email }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Container -->
      <div class="chat-container">
        <!-- Chat Header (like a group chat header) -->
        <div class="chat-internal-header">
          <div class="user-info-bar">
            <ion-icon :icon="icons.personCircle || icons.person" class="header-avatar" />
            <div class="header-text">
              <span class="header-name">{{ conversationData.user_name || conversationData.guest_name }}</span>
              <span class="header-status">Ticket #{{ conversationData.id.toString().substring(0, 8) }}</span>
            </div>
          </div>
          <ion-button class="scroll-to-bottom-btn" fill="clear" @click="scrollToBottom">
            <ion-icon :icon="icons.chevronDown" />
          </ion-button>
        </div>

        <div class="chat-window">
          <!-- Comments list (cascade) -->
          <div class="comments-section">
            <div class="comments-cascade">
              <template v-for="(item, index) in groupedComments" :key="item.type === 'date' ? 'date-' + index : item.id">
                <!-- Date Separator -->
                <div v-if="item.type === 'date'" class="date-separator">
                  <span>{{ item.value }}</span>
                </div>

                <!-- Message Row -->
                <div
                  v-else
                  class="message-row"
                  :class="{ 'message-mine': isCurrentUserComment(item), 'message-theirs': !isCurrentUserComment(item) }"
                >
                  <div class="message-bubble">
                    <div class="message-sender" v-if="!isCurrentUserComment(item)">
                      {{ item.guest_name || item.user_name || 'User' }}
                      <span v-if="item.response" class="support-tag">Support</span>
                    </div>
                    <div class="message-text">
                      <span v-if="item.isOriginal" class="original-tag">Initial Request</span>
                      {{ item.content || item.text || '' }}
                    </div>
                    
                    <!-- Comment attachments if any -->
                    <div v-if="item.attachments && item.attachments.length" class="message-attachments">
                      <a
                        v-for="att in item.attachments"
                        :key="att.id"
                        :href="getAttachmentUrl(att.file)"
                        target="_blank"
                        rel="noopener"
                        class="attachment-link"
                      >
                        <ion-icon :icon="documentAttachOutline" />
                        <span>{{ getAttachmentName(att.file) }}</span>
                      </a>
                    </div>

                    <div class="message-footer">
                      <span class="message-time">{{ formatTime(item.created_at) }}</span>
                      <ion-icon v-if="isCurrentUserComment(item)" :icon="checkmarkCircleOutline" class="status-icon" />
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Sticky Footer Area (Moved outside of Card) -->
      <footer class="conversation-sticky-footer">
        <!-- Sticky input area -->
        <div class="chat-input-bar">
          <div v-if="commentError" class="error-line">{{ commentError }}</div>
          <div v-if="commentSuccess" class="success-line">{{ commentSuccess }}</div>
          
          <div v-if="isTicketResolved" class="ticket-resolved-banner">
            <ion-icon :icon="icons.checkmarkCircle" />
            <span>Ticket Resolved</span>
          </div>

          <div class="input-container" v-else>
            <textarea
              v-model="newComment"
              placeholder="Type a message..."
              rows="1"
              class="message-textarea"
              :disabled="sendingComment"
              @keydown.ctrl.enter="sendComment"
              @keydown.meta.enter="sendComment"
            ></textarea>

            <div class="action-buttons">
              <ion-button 
                fill="clear"
                class="icon-btn"
                @click="triggerFilePicker"
                :disabled="sendingComment"
              >
                <ion-icon :icon="attachOutline" slot="icon-only" />
              </ion-button>

              <ion-button 
                class="send-btn"
                @click="sendComment" 
                :disabled="!newComment.trim() || sendingComment"
              >
                <ion-spinner v-if="sendingComment" name="dots" color="light" />
                <ion-icon v-else :icon="sendOutline" slot="icon-only" color="light" />
              </ion-button>
            </div>
          </div>

          <div v-if="selectedFile" class="file-preview-bar">
            <ion-icon :icon="documentAttachOutline" />
            <span class="file-name">{{ selectedFile.name }}</span>
            <ion-button fill="clear" size="small" class="remove-file-btn" @click="removeFile">
              <ion-icon :icon="closeCircleOutline" slot="icon-only" />
            </ion-button>
          </div>
          
          <div v-if="fileError" class="error-text small">{{ fileError }}</div>
        </div>

        <!-- Support Actions -->
        <div class="support-actions" v-if="auth.isSupportUser && normalizedStatus !== 'resolved'">
          <ion-button 
            color="success"
            fill="clear"
            size="small"
            @click="resolveTicket"
            :disabled="updatingStatus"
          >
            <ion-icon :icon="checkmarkCircleOutline" slot="start" />
            Mark as Resolved
          </ion-button>
        </div>
      </footer>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <ion-icon :icon="icons.chatbubbleEllipses" class="empty-icon" />
      <p>No conversation data available</p>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import { IonSpinner, IonIcon, IonBadge, IonButton, IonTextarea, onIonViewWillEnter } from '@ionic/vue';
import { attachOutline, sendOutline, checkmarkCircleOutline, documentAttachOutline, closeCircleOutline } from 'ionicons/icons';
import API from '@/utils/api/api';

// Icons
const icons = inject('icons', {});

// Route
const route = useRoute();
const ticketId = ref(null);

// Profile: 'dev' (default) or 'prod' - read from env (Vite)
// Use VITE_PROFILE or VITE_APP_PROFILE to set. Defaults to 'dev'.
const PROFILE = (import.meta.env.VITE_APP_PROFILE || 'dev').toLowerCase();

// Auth store
const auth = useAuthStore();
const currentUserId = computed(() => auth.userId);

// State
const conversationData = ref(null);
const loading = ref(false);
const error = ref('');
const newComment = ref('');
const sendingComment = ref(false);
const commentError = ref('');
const commentSuccess = ref('');

// Guest user info (for non-authenticated users accessing via token)
const guestUserName = ref(null);
const guestUserEmail = ref(null);
// Ticket user ID (from the original ticket creator)
const ticketUserId = ref(null);

// Ticket status state
const updatingStatus = ref(false);
const statusError = ref('');

// File state
const selectedFile = ref(null);
const fileInputRef = ref(null);
const fileError = ref('');
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

// Computed: Grouped comments with date separators
const groupedComments = computed(() => {
  const groups = [];
  
  if (!conversationData.value) return [];

  const allMessages = [];
  
  // Add original ticket as the first message
  allMessages.push({
    id: 'original',
    content: conversationData.value.description,
    created_at: conversationData.value.created_at,
    user_name: conversationData.value.user_name,
    guest_name: conversationData.value.guest_name,
    guest_email: conversationData.value.guest_email,
    attachments: conversationData.value.attachments || [],
    isOriginal: true,
    user: conversationData.value.user
  });

  // Add all comments
  if (conversationData.value.comments) {
    const sorted = [...conversationData.value.comments].sort((a, b) => {
      return new Date(a.created_at) - new Date(b.created_at);
    });
    allMessages.push(...sorted);
  }
  
  let lastDate = null;
  
  allMessages.forEach(item => {
    const date = new Date(item.created_at).toLocaleDateString(undefined, { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
    
    if (date !== lastDate) {
      groups.push({ type: 'date', value: date });
      lastDate = date;
    }
    groups.push({ type: 'message', ...item });
  });
  
  return groups;
});

// Computed: Normalized ticket status (lowercase)
// Backend returns "Open", "In Progress", "Resolved"
// We need to compare with "open", "in_progress", "resolved"
const normalizedStatus = computed(() => {
  return conversationData.value?.status?.toLowerCase().replace(/ /g, '_') || '';
});

// Computed: Check if ticket is resolved (conversation closed)
const isTicketResolved = computed(() => {
  return normalizedStatus.value === 'resolved';
});

// Computed: Current user display name (auth.username or guest_name)
const currentUserDisplayName = computed(() => {
  // If logged in, use auth username
  if (auth.username) {
    return auth.username;
  }
  // Otherwise use guest name from conversation data
  return guestUserName.value || conversationData.value?.guest_name || 'Guest';
});

// Function: Check if a comment is from current user
const isCurrentUserComment = (comment) => {
  // If we are in dev mode and it's mock data, we use names as a fallback
  if (PROFILE === 'dev' && !currentUserId.value) {
    // In mock data, "Dev User" is the "owner"
    if (comment.user_name === 'Dev User' || (comment.isOriginal && !comment.response)) {
      return true;
    }
    return false;
  }

  // Priority 1: Authenticated users (logged in) - compare with currentUserId
  if (currentUserId.value && comment.user) {
    const commentUserId = typeof comment.user === 'object' ? comment.user.id : comment.user;
    const currentUserIdVal = currentUserId.value;
    
    if (String(commentUserId) === String(currentUserIdVal)) {
      return true;
    }
  }
  
  // Priority 2: Match by Support status (if agent is viewing)
  if (auth.isSupportUser && comment.response === true) {
    // If the comment is a support response and current user is support,
    // we check if the name matches to avoid putting other agents' messages on the right
    if (comment.user_name === auth.username) return true;
  }

  // Priority 3: User accessing via token (not logged in) - compare with ticketUserId
  if (!currentUserId.value && ticketUserId.value && comment.user) {
    const commentUserId = typeof comment.user === 'object' ? comment.user.id : comment.user;
    if (String(commentUserId) === String(ticketUserId.value)) return true;
  }
  
  // Priority 4: Guest users - compare guest info
  if (!currentUserId.value && guestUserEmail.value && comment.guest_email) {
    if (comment.guest_email === guestUserEmail.value) return true;
  }

  // Priority 5: Original ticket logic
  if (comment.isOriginal) {
    if (currentUserId.value && conversationData.value?.user) {
      const tid = typeof conversationData.value.user === 'object' ? conversationData.value.user.id : conversationData.value.user;
      if (String(tid) === String(currentUserId.value)) return true;
    }
    if (guestUserEmail.value && conversationData.value?.guest_email === guestUserEmail.value) {
      return true;
    }
  }
  
  return false;
};

// CSRF Token Management
// Function helper para obtener el valor de una cookie
const getCookieValue = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
};

// Function helper para obtener headers con CSRF token
const getHeadersWithCSRF = (additionalHeaders = {}) => {
  const csrfToken = getCookieValue('csrftoken');
  const headers = { ...additionalHeaders };
  
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
    console.log('🛡️ CSRF Token agregado al header:', csrfToken);
  } else {
    console.warn('⚠️ No se encontró CSRF token en las cookies');
  }
  
  return headers;
};

// Function para obtener CSRF token si no existe
const ensureCSRFToken = async () => {
  let csrfToken = getCookieValue('csrftoken');
  if (!csrfToken) {
    console.log('🛡️ No hay CSRF token, obteniendo uno...');
    try {
      await API.get(API.CSRF_TOKEN);
      // Pequeña pausa para que se establezca la cookie
      await new Promise(resolve => setTimeout(resolve, 500));
      csrfToken = getCookieValue('csrftoken');
      if (csrfToken) {
        console.log('✅ CSRF token obtenido exitosamente');
      }
    } catch (err) {
      console.error('❌ Error obteniendo CSRF token:', err);
    }
  }
  return csrfToken;
};

// Helper: returns a mock conversation object used in dev profile for UI work without backend access
function getMockConversation() {
  const now = new Date().toISOString();
  return {
    id: 'dev-0001',
    title: 'Sample Ticket (Dev Mode)',
    priority: 'Medium',
    status: 'Open',
    created_at: now,
    updated_at: now,
    user_name: 'Dev User',
    description: 'This is mock conversation data used in development mode to allow UI tweaks without backend access.',
    organization: 'Dev Org',
    assigned_to_name: 'Support Agent',
    category: 'General',
    infrastructure_category: 'N/A',
    machine_type: 'N/A',
    electric_machine_subtype: null,
    mechanical_machine_subtype: null,
    guest_name: 'Guest Dev',
    guest_email: 'dev@example.com',
    attachments: [],
    comments: [
      {
        id: 'c-dev-1',
        content: 'This is a mock comment from the user.',
        created_at: now,
        user_name: 'Dev User',
        guest_name: null,
        attachments: [],
        response: false
      },
      {
        id: 'c-dev-2',
        content: 'This is a mock response from support.',
        created_at: now,
        user_name: null,
        guest_name: 'Support',
        attachments: [],
        response: true
      }
    ]
  };
}

// Get ticket ID from query params or verify token
const initializeConversation = async () => {
  console.log('🔄 Initializing/Reloading conversation...');
  const token = route.query.token;
  const id = route.query.id;

  // Dev profile shortcut: skip token/id verification to allow UI-only work
  if (PROFILE === 'dev' && !id && !token) {
    console.log('⚙️ Dev profile: Loading mock conversation');
    conversationData.value = getMockConversation();
    loading.value = false;
    setTimeout(() => scrollToBottom(), 500);
    return;
  }

  if (token) {
    // Verify token and get ticket_id
    loading.value = true;
    try {
      await ensureCSRFToken();
      const headers = getHeadersWithCSRF();
      const response = await API.post(API.COMMENT_TOKEN_VERIFICATION, { token }, headers);
      const responseData = Array.isArray(response) ? response[0] : response;
      const verifiedTicketId = responseData?.ticket_id;
      
      if (verifiedTicketId) {
        ticketId.value = verifiedTicketId;
        await loadConversation();
      } else {
        error.value = 'Invalid or expired token';
      }
    } catch (err) {
      console.error('Error verifying token:', err);
      error.value = err?.message || 'Failed to verify access token';
    } finally {
      loading.value = false;
    }
  } else if (id) {
    ticketId.value = id;
    await loadConversation();
  } else {
    error.value = 'No ticket ID or access token provided';
  }
};

onMounted(async () => {
  await initializeConversation();

  // Store current scroll position to prevent movement
  let scrollPosition = window.scrollY;
  
  // Prevent any scroll caused by focusing textarea
  const handleFocus = () => {
    window.scrollTo(0, scrollPosition);
  };
  
  const handleScroll = () => {
    scrollPosition = window.scrollY;
  };
  
  window.addEventListener('scroll', handleScroll);
  window.addEventListener('focusin', handleFocus);
});

// Ensure reload when entering view (crucial for Ionic/Mobile app caching)
onIonViewWillEnter(() => {
  console.log('📱 Page entering view - triggering refresh');
  initializeConversation();
});

// Watch for changes in ticket ID or token (handles internal navigation)
watch(() => [route.query.id, route.query.token], async () => {
  await initializeConversation();
});

// Load conversation data
async function loadConversation() {
  if (!ticketId.value) return;
  
  loading.value = true;
  error.value = '';
  
  try {
    const endpoint = API.TICKET_CONVERSATION(ticketId.value);
    const data = await API.get(endpoint);
    // API.get returns an array, get first element
    conversationData.value = Array.isArray(data) ? data[0] : data;
    
    console.log('📋 Conversation data loaded:', conversationData.value);
    
    // Extract user ID from ticket (if exists)
    if (conversationData.value?.user) {
      ticketUserId.value = conversationData.value.user;
      console.log('👤 Ticket user ID:', ticketUserId.value);
    }
    
    // Extract guest info from ticket (if exists)
    if (conversationData.value?.guest_name) {
      guestUserName.value = conversationData.value.guest_name;
      guestUserEmail.value = conversationData.value.guest_email;
      console.log('👥 Guest user info:', { name: guestUserName.value, email: guestUserEmail.value });
    }
    
    // Auto-scroll to bottom after conversation loads
    setTimeout(() => {
      scrollToBottom();
    }, 500);
  } catch (err) {
    console.error('Error loading conversation:', err);
    error.value = err?.message || 'Failed to load conversation';
  } finally {
    loading.value = false;
  }
}

// Send new comment
async function sendComment() {
  if (!newComment.value.trim() || sendingComment.value) return;
  
  // Validate ticket ID
  if (!ticketId.value) {
    commentError.value = 'Invalid ticket ID';
    return;
  }
  
  // Validate user identity (authenticated user, ticket user, or guest)
  if (!currentUserId.value && !ticketUserId.value && !guestUserName.value) {
    commentError.value = 'User identity not available';
    return;
  }
  
  sendingComment.value = true;
  commentError.value = '';
  commentSuccess.value = '';
  
  try {
    // Ensure CSRF token exists before posting
    await ensureCSRFToken();
    
    // Step 1: Create comment
    // response is true for support agents, false for normal users
    const commentData = {
      response: auth.isSupportUser,
      content: newComment.value.trim(),
      ticket: ticketId.value, // UUID string, not a number
    };
    
    // Priority: 1. Authenticated user, 2. Ticket user ID, 3. Guest info
    if (currentUserId.value) {
      // If currently authenticated, use that user
      commentData.user = currentUserId.value;
      console.log('Sending as authenticated user:', currentUserId.value);
    } else if (ticketUserId.value) {
      // If ticket has a user ID, use it
      commentData.user = ticketUserId.value;
      console.log('Sending as ticket user:', ticketUserId.value);
    } else if (guestUserName.value && guestUserEmail.value) {
      // Otherwise use guest info
      commentData.guest_name = guestUserName.value;
      commentData.guest_email = guestUserEmail.value;
      console.log('Sending as guest:', { name: guestUserName.value, email: guestUserEmail.value });
    }
    
    console.log('Sending comment:', commentData);
    const headers = getHeadersWithCSRF();
    const commentResponse = await API.post(API.COMMENT, commentData, headers);
    
    // Extract comment ID from response
    const commentId = Array.isArray(commentResponse) 
      ? commentResponse[0]?.id 
      : commentResponse?.id;
    
    console.log('Comment created with ID:', commentId);
    
    // Step 2: If support agent, change ticket status to "in_progress"
    console.log('Checking status update conditions:');
    console.log('- Is support user:', auth.isSupportUser);
    console.log('- Current ticket status:', conversationData.value?.status);
    console.log('- Normalized status:', normalizedStatus.value);
    
    if (auth.isSupportUser && normalizedStatus.value === 'open') {
      try {
        console.log('Changing ticket status to in_progress...');
        await updateTicketStatus('in_progress');
        console.log('Status update completed successfully');
      } catch (statusErr) {
        console.error('Error updating ticket status:', statusErr);
        // Don't block comment submission if status update fails
      }
    } else {
      console.log('Status update skipped - conditions not met');
    }
    
    // Step 3: Upload attachment if file is selected
    if (selectedFile.value && commentId) {
      try {
        await uploadAttachment(commentId, selectedFile.value);
        commentSuccess.value = 'Comment and attachment sent successfully';
      } catch (attachErr) {
        console.error('Error uploading attachment:', attachErr);
        commentSuccess.value = 'Comment sent, but attachment upload failed';
      }
    } else {
      commentSuccess.value = 'Comment sent successfully';
    }
    
    // Clear form
    newComment.value = '';
    removeFile();
    
    // Reload conversation to show new comment
    await loadConversation();
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      commentSuccess.value = '';
    }, 3000);
  } catch (err) {
    console.error('Error sending comment:', err);
    commentError.value = err?.message || 'Failed to send comment';
  } finally {
    sendingComment.value = false;
  }
}

// Upload attachment for comment
async function uploadAttachment(commentId, file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('comment', String(commentId));
  
  console.log('Uploading attachment for comment:', commentId);
  const headers = getHeadersWithCSRF();
  const response = await API.post(API.COMMENT_ATTACHMENT, formData, headers);
  console.log('Attachment uploaded:', response);
  return response;
}

// Update ticket status (PATCH)
async function updateTicketStatus(newStatus) {
  if (!ticketId.value) {
    console.error('Cannot update status: no ticket ID');
    return;
  }
  
  try {
    // Ensure CSRF token exists before patching
    await ensureCSRFToken();
    
    const endpoint = `${API.SUPPORT_TICKET}${ticketId.value}/`;
    console.log('Updating ticket status:');
    console.log('- Endpoint:', endpoint);
    console.log('- New status:', newStatus);
    console.log('- Payload:', { status: newStatus });
    
    const headers = getHeadersWithCSRF();
    const response = await API.patch(endpoint, { status: newStatus }, headers);
    console.log('PATCH response:', response);
    console.log(`Ticket status updated to: ${newStatus}`);
    
    // Update local state
    if (conversationData.value) {
      conversationData.value.status = newStatus;
      console.log('Local state updated');
    }
  } catch (err) {
    console.error('Error updating ticket status:', err);
    console.error('Error details:', err.response || err.message);
    throw err;
  }
}

// Resolve ticket (with confirmation)
async function resolveTicket() {
  if (!ticketId.value || updatingStatus.value) return;
  
  // Confirmation dialog
  const confirmed = confirm('Are you sure you want to mark this ticket as resolved? This indicates the issue has been fully addressed.');
  
  if (!confirmed) return;
  
  updatingStatus.value = true;
  statusError.value = '';
  
  try {
    await updateTicketStatus('resolved');
    commentSuccess.value = 'Ticket marked as resolved';
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      commentSuccess.value = '';
    }, 3000);
  } catch (err) {
    console.error('Error resolving ticket:', err);
    statusError.value = err?.message || 'Failed to resolve ticket';
  } finally {
    updatingStatus.value = false;
  }
}

// File handling functions
function triggerFilePicker() {
  fileInputRef.value?.click();
}

function handleFileChange(e) {
  const file = e.target.files?.[0];
  fileError.value = '';
  
  if (!file) {
    selectedFile.value = null;
    return;
  }
  
  // Validate file size
  if (file.size > MAX_FILE_SIZE) {
    fileError.value = `File is too large. Max size: ${formatFileSize(MAX_FILE_SIZE)}`;
    if (fileInputRef.value) fileInputRef.value.value = '';
    selectedFile.value = null;
    return;
  }
  
  // Validate file type
  const allowed = ['image/png', 'image/jpg', 'image/jpeg', 'application/pdf', 
                   'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                   'text/plain'];
  const ext = file.name.split('.').pop()?.toLowerCase() || '';
  const accepts = '.png,.jpg,.jpeg,.pdf,.doc,.docx,.txt';
  
  if (!allowed.includes(file.type) && !accepts.includes(`.${ext}`)) {
    fileError.value = 'Unsupported file type. Allowed: PNG, JPG, JPEG, PDF, DOC, DOCX, TXT';
    if (fileInputRef.value) fileInputRef.value.value = '';
    selectedFile.value = null;
    return;
  }
  
  selectedFile.value = file;
}

function removeFile() {
  selectedFile.value = null;
  fileError.value = '';
  if (fileInputRef.value) fileInputRef.value.value = '';
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

// Helper functions
function priorityColor(priority) {
  const colors = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  };
  return colors[priority?.toLowerCase()] || 'medium';
}

function statusColor(status) {
  const colors = {
    open: 'primary',
    'in progress': 'warning',
    resolved: 'success',
    closed: 'medium'
  };
  return colors[status?.toLowerCase()] || 'medium';
}

function formatTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
}

function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  });
}

function getAttachmentUrl(filePath) {
  if (!filePath) return '';
  if (filePath.startsWith('http')) return filePath;
  
  // Get base URL from API
  const baseUrl = API.API_BASE_URL.replace('/api/v1', '');
  return `${baseUrl}${filePath}`;
}

function getAttachmentName(filePath) {
  if (!filePath) return 'attachment';
  const parts = filePath.split('/');
  const filename = parts[parts.length - 1];
  try {
    return decodeURIComponent(filename);
  } catch {
    return filename;
  }
}

// Scroll to bottom (comment input section)
function scrollToBottom() {
  setTimeout(() => {
    const chatWindow = document.querySelector('.chat-window');
    if (chatWindow) {
      chatWindow.scrollTo({
        top: chatWindow.scrollHeight,
        behavior: 'smooth'
      });
      return;
    }

    const commentSection = document.querySelector('.comment-input-section');
    if (commentSection) {
      commentSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      window.scrollTo({
        top: document.documentElement.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, 100);
}
</script>

<style scoped>
.conversation-form {
  width: 100%;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.conversation-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 0;
  padding-bottom: 160px; /* Space for the floating footer */
  width: 100%;
}

.ticket-header-compact {
  width: 100%;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 24px 0;
  margin: 0;
}

.header-inner {
  max-width: 1400px;
  width: calc(100% - 48px);
  margin: 0 auto;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ticket-id {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--ion-color-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.header-main h2 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.header-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: #64748b;
}

.detail-item ion-icon {
  font-size: 1rem;
  color: var(--ion-color-primary);
}

.header-meta {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.chat-container {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: none;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  border-radius: 0;
  box-shadow: none;
  overflow: hidden;
  margin-top: 0;
  flex: 1;
  width: 100%;
}

.chat-internal-header {
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  color: #334155;
  display: flex;
  justify-content: center;
  align-items: center;
}

.user-info-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 1400px;
  width: 100%;
  justify-content: space-between;
}

.header-avatar {
  font-size: 2.2rem;
  color: var(--ion-color-primary);
}

.header-text {
  display: flex;
  flex-direction: column;
}

.header-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: #1e293b;
}

.header-status {
  font-size: 0.75rem;
  color: #64748b;
}

.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 32px 0;
  background-color: #f3f4f6;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.comments-section {
  max-width: 1400px;
  width: calc(100% - 48px);
  display: flex;
  flex-direction: column;
}

.date-separator {
  display: flex;
  justify-content: center;
  margin: 24px 0;
  position: sticky;
  top: 0;
  z-index: 5;
}

.date-separator span {
  background: #e2e8f0;
  color: #475569;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.comments-cascade {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-row {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.message-mine {
  align-items: flex-end;
}

.message-theirs {
  align-items: flex-start;
}

/* Original Request Special Styling */
.message-row:first-child .message-bubble {
  border-left: 5px solid var(--ion-color-primary);
  border-radius: 12px;
  max-width: 95%;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.08);
}

.message-row:first-child .message-sender {
  color: var(--ion-color-primary);
}

.message-bubble {
  max-width: 85%;
  padding: 14px 18px;
  border-radius: 18px;
  font-size: 0.95rem;
  line-height: 1.5;
  position: relative;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  margin-bottom: 4px;
}

.message-mine .message-bubble {
  background: var(--ion-color-primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-mine .message-sender {
  color: rgba(255, 255, 255, 0.9);
  text-align: right;
}

.message-theirs .message-bubble {
  background: white;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 4px;
}

.message-sender {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--ion-color-primary);
  margin-bottom: 4px;
}

.message-mine .message-sender {
  color: rgba(255, 255, 255, 0.9);
}

.message-text {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
  gap: 4px;
  align-items: center;
}

.message-time {
  font-size: 0.65rem;
  color: #64748b;
}

.message-mine .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.status-icon {
  font-size: 0.9rem;
  color: white;
}

.support-tag, .original-tag {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 700;
  text-transform: uppercase;
  margin-left: 6px;
}

.support-tag {
  background: #0ea5e9;
  color: white;
}

.original-tag {
  background: var(--ion-color-primary);
  color: white;
}

.chat-input-bar {
  padding: 0;
  background: transparent;
  width: 100%;
}

.input-container {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.message-textarea {
  flex: 1;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 0.95rem;
  max-height: 120px;
  resize: none;
  color: #1e293b;
  outline: none;
  transition: all 0.2s;
}

.message-textarea:focus {
  border-color: var(--ion-color-primary);
  background: white;
  box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.1);
}

.send-btn {
  --background: var(--ion-color-primary);
  --background-hover: var(--ion-color-primary-shade);
  --border-radius: 12px;
  width: 48px;
  height: 48px;
  margin: 0;
  flex-shrink: 0;
}

/* Floating Footer for conversation actions */
.conversation-sticky-footer {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 48px);
  max-width: 1400px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  padding: 12px 20px;
}

.loading-container,
.error-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.error-icon,
.empty-icon {
  font-size: 3rem;
  color: #cbd5e1;
  margin-bottom: 12px;
}

.error-text {
  color: #ef4444;
}

.support-actions {
  display: flex;
  justify-content: center;
  padding: 8px 0 0 0;
  background: transparent;
}

.ticket-date {
  font-weight: 500;
}

.original-ticket {
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border: 2px solid #fdba74;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
  box-shadow: 0 4px 6px -1px rgba(249, 115, 22, 0.1), 0 2px 4px -1px rgba(249, 115, 22, 0.06);
}

.message-header {
  margin-bottom: 16px;
}

.message-attachments {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.attachment-link {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  font-size: 0.8rem;
  color: #0284c7;
  padding: 6px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 6px;
  transition: background 0.2s;
}

.attachment-link:hover {
  background: rgba(0, 0, 0, 0.06);
}

.action-buttons {
  display: flex;
  align-items: center;
}

.icon-btn {
  --padding-start: 8px;
  --padding-end: 8px;
  margin: 0;
  color: #64748b;
  font-size: 1.4rem;
}

.file-preview-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 12px;
  padding: 6px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.8rem;
}

.file-name {
  flex: 1;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.remove-file-btn {
  --color: #ef4444;
  margin: 0;
  height: 24px;
  font-size: 0.8rem;
}

.ticket-resolved-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  background: #ecfdf5;
  color: #065f46;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.85rem;
  margin: 10px;
}

.error-line, .success-line {
  font-size: 0.75rem;
  padding: 4px 12px;
  text-align: center;
}

.error-line { color: #ef4444; }
.success-line { color: #10b981; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .chat-container {
    height: calc(100vh - 80px);
    margin-top: 0;
    border-radius: 0;
    border: none;
  }

  .message-bubble {
    max-width: 92%;
  }
}
</style>
