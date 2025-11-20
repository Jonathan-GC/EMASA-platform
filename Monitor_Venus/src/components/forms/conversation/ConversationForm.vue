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

    <!-- Conversation loaded -->
    <div v-else-if="conversationData" class="conversation-content">
      <!-- Ticket header -->
      <div class="ticket-header">
        <div class="header-top">
          <h2>{{ conversationData.title }}</h2>
          <div class="ticket-badges">
            <ion-badge :color="priorityColor(conversationData.priority)">
              {{ conversationData.priority }}
            </ion-badge>
            <ion-badge :color="statusColor(conversationData.status)">
              {{ conversationData.status }}
            </ion-badge>
          </div>
        </div>
        <div class="header-subtitle">
          <span class="ticket-date">Created {{ formatDate(conversationData.created_at) }}</span>
          <span v-if="conversationData.updated_at !== conversationData.created_at" class="ticket-date"> • Updated {{ formatDate(conversationData.updated_at) }}</span>
        </div>
      </div>

      <!-- Original ticket message -->
      <div class="original-ticket">
        <div class="message-header">
          <div class="user-info">
            <ion-icon :icon="icons.personCircle" class="avatar-icon" />
            <div class="user-details">
              <div class="user-name-row">
                <strong>{{ conversationData.user_name }}</strong>
                <span class="badge-original">Original Ticket</span>
              </div>
              <div class="message-date">{{ formatDate(conversationData.created_at) }}</div>
            </div>
          </div>
        </div>

        <!-- Ticket Description -->
        <div class="message-content">
          <p>{{ conversationData.description }}</p>
        </div>

        <!-- Ticket Metadata Grid -->
        <div class="ticket-metadata">
          <div class="metadata-item" v-if="conversationData.organization">
            <ion-icon :icon="icons.business || icons.briefcase" />
            <div>
              <span class="metadata-label">Organization</span>
              <span class="metadata-value">{{ conversationData.organization }}</span>
            </div>
          </div>
          
          <div class="metadata-item" v-if="conversationData.assigned_to_name">
            <ion-icon :icon="icons.personAdd || icons.person" />
            <div>
              <span class="metadata-label">Assigned to</span>
              <span class="metadata-value">{{ conversationData.assigned_to_name }}</span>
            </div>
          </div>

          <div class="metadata-item" v-if="conversationData.category">
            <ion-icon :icon="icons.pricetag || icons.bookmark" />
            <div>
              <span class="metadata-label">Category</span>
              <span class="metadata-value">{{ conversationData.category }}</span>
            </div>
          </div>

          <div class="metadata-item" v-if="conversationData.infrastructure_category">
            <ion-icon :icon="icons.hardware || icons.construct" />
            <div>
              <span class="metadata-label">Infrastructure</span>
              <span class="metadata-value">{{ conversationData.infrastructure_category }}</span>
            </div>
          </div>

          <div class="metadata-item" v-if="conversationData.machine_type">
            <ion-icon :icon="icons.cog || icons.settings" />
            <div>
              <span class="metadata-label">Machine Type</span>
              <span class="metadata-value">{{ conversationData.machine_type }}</span>
            </div>
          </div>

          <div class="metadata-item" v-if="conversationData.electric_machine_subtype">
            <ion-icon :icon="icons.flash || icons.bolt" />
            <div>
              <span class="metadata-label">Electric Subtype</span>
              <span class="metadata-value">{{ conversationData.electric_machine_subtype }}</span>
            </div>
          </div>

          <div class="metadata-item" v-if="conversationData.mechanical_machine_subtype">
            <ion-icon :icon="icons.construct || icons.build" />
            <div>
              <span class="metadata-label">Mechanical Subtype</span>
              <span class="metadata-value">{{ conversationData.mechanical_machine_subtype }}</span>
            </div>
          </div>

          <div class="metadata-item" v-if="conversationData.guest_name">
            <ion-icon :icon="icons.personCircle || icons.person" />
            <div>
              <span class="metadata-label">Guest Name</span>
              <span class="metadata-value">{{ conversationData.guest_name }}</span>
            </div>
          </div>

          <div class="metadata-item" v-if="conversationData.guest_email">
            <ion-icon :icon="icons.mail || icons.mailOutline" />
            <div>
              <span class="metadata-label">Guest Email</span>
              <span class="metadata-value">{{ conversationData.guest_email }}</span>
            </div>
          </div>
        </div>

        <!-- Attachments -->
        <div v-if="conversationData.attachments && conversationData.attachments.length" class="ticket-attachments">
          <div class="attachments-header">
            <ion-icon :icon="icons.attach || icons.document" />
            <strong>Attachments ({{ conversationData.attachments.length }})</strong>
          </div>
          <div class="attachments-grid">
            <a
              v-for="att in conversationData.attachments"
              :key="att.id"
              :href="getAttachmentUrl(att.file)"
              target="_blank"
              rel="noopener"
              class="attachment-card"
            >
              <ion-icon :icon="icons.documentText || icons.document" class="attachment-icon" />
              <div class="attachment-info">
                <span class="attachment-name">{{ getAttachmentName(att.file) }}</span>
                <span class="attachment-date">{{ formatDate(att.uploaded_at) }}</span>
              </div>
            </a>
          </div>
        </div>
      </div>

      <!-- Conversation divider -->
      <div class="conversation-divider">
        <span>─── Conversation ───</span>
      </div>

      <!-- Comments list (cascade) -->
      <div class="comments-section">
        <div v-if="!conversationData.comments || conversationData.comments.length === 0" class="no-comments">
          <ion-icon :icon="icons.chatbubbles || icons.chatboxEllipses" class="empty-icon" />
          <p>No responses yet. Start the conversation!</p>
        </div>
        
        <div v-else class="comments-cascade">
          <div
            v-for="(comment, index) in sortedComments"
            :key="comment.id"
            class="comment-bubble"
            :class="{ 'comment-current-user': isCurrentUserComment(comment), 'comment-other-user': !isCurrentUserComment(comment) }"
          >
            <div class="bubble-header">
              <ion-icon :icon="icons.personCircle || icons.person" class="bubble-avatar" />
              <div class="bubble-info">
                <strong class="bubble-user-name">{{ comment.user_name || 'Unknown User' }}</strong>
                <span class="bubble-date">{{ formatDate(comment.created_at) }}</span>
              </div>
            </div>
            <div class="bubble-content">
              <p>{{ comment.content || comment.text || '' }}</p>
            </div>
            <!-- Comment attachments if any -->
            <div v-if="comment.attachments && comment.attachments.length" class="bubble-attachments">
              <div class="bubble-attachments-header">
                <ion-icon :icon="icons.attach || icons.document" />
                <span>{{ comment.attachments.length }} file(s)</span>
              </div>
              <div class="bubble-attachments-list">
                <a
                  v-for="att in comment.attachments"
                  :key="att.id"
                  :href="getAttachmentUrl(att.file)"
                  target="_blank"
                  rel="noopener"
                  class="bubble-attachment-item"
                >
                  <ion-icon :icon="icons.documentText || icons.document" />
                  <span>{{ getAttachmentName(att.file) }}</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- New comment input -->
      <div class="comment-input-section">
        <div v-if="commentError" class="error-line">{{ commentError }}</div>
        <div v-if="commentSuccess" class="success-line">{{ commentSuccess }}</div>
        
        <textarea
          v-model="newComment"
          placeholder="Write your response..."
          rows="3"
          class="comment-textarea"
          @keydown.ctrl.enter="sendComment"
          @keydown.meta.enter="sendComment"
        ></textarea>
        
        <!-- File preview (if selected) -->
        <div v-if="selectedFile" class="file-preview-compact">
          <ion-icon :icon="icons.documentText || icons.document" />
          <span class="file-name">{{ selectedFile.name }}</span>
          <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
          <ion-button
            fill="clear"
            size="small"
            color="danger"
            @click="removeFile"
            :disabled="sendingComment"
          >
            <ion-icon :icon="icons.close" slot="icon-only" />
          </ion-button>
        </div>
        
        <div v-if="fileError" class="file-error-compact">{{ fileError }}</div>
        
        <div v-if="statusError" class="error-line">{{ statusError }}</div>
        
        <!-- Actions row with attachment, send, and resolve -->
        <div class="comment-actions">
          <input
            ref="fileInputRef"
            type="file"
            class="hidden-input"
            accept=".png,.jpg,.jpeg,.pdf,.doc,.docx,.txt"
            @change="handleFileChange"
          />
          <ion-button 
            fill="clear"
            size="small"
            color="medium"
            @click="triggerFilePicker"
            :disabled="sendingComment"
          >
            <ion-icon :icon="icons.attach || icons.document" slot="icon-only" />
          </ion-button>
          
          <ion-button 
            color="warning"
            @click="sendComment" 
            :disabled="!newComment.trim() || sendingComment"
            expand="block"
            class="send-button"
          >
            <ion-spinner v-if="sendingComment" name="dots" />
            <ion-icon v-else :icon="icons.send" slot="start" />
            {{ sendingComment ? 'Sending...' : 'Send' }}
          </ion-button>
          
          <!-- Resolve button (only for support agents and if ticket is not already resolved) -->
          <ion-button 
            v-if="auth.isSupportUser && normalizedStatus !== 'resolved'"
            color="success"
            fill="outline"
            @click="resolveTicket"
            :disabled="updatingStatus"
            class="resolve-button"
          >
            <ion-spinner v-if="updatingStatus" name="dots" />
            <ion-icon v-else :icon="icons.checkmarkCircle || icons.checkmark" slot="start" />
            {{ updatingStatus ? 'Resolving...' : 'Resolve' }}
          </ion-button>
        </div>
      </div>
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
import { IonSpinner, IonIcon, IonBadge, IonButton, IonTextarea } from '@ionic/vue';
import API from '@/utils/api/api';

// Icons
const icons = inject('icons', {});

// Route
const route = useRoute();
const ticketId = ref(null);

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

// Computed: Sort comments by date (oldest first)
const sortedComments = computed(() => {
  if (!conversationData.value?.comments) return [];
  return [...conversationData.value.comments].sort((a, b) => {
    return new Date(a.created_at) - new Date(b.created_at);
  });
});

// Computed: Normalized ticket status (lowercase)
// Backend returns "Open", "In Progress", "Resolved"
// We need to compare with "open", "in_progress", "resolved"
const normalizedStatus = computed(() => {
  return conversationData.value?.status?.toLowerCase().replace(/ /g, '_') || '';
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
  // If logged in, compare with user ID from comment
  if (currentUserId.value && comment.user) {
    return comment.user === currentUserId.value;
  }
  
  // If accessing via token (ticket user), compare with ticket user ID
  if (ticketUserId.value && comment.user) {
    return comment.user === ticketUserId.value;
  }
  
  // For guests, compare guest_name and guest_email
  if (guestUserName.value && guestUserEmail.value && comment.guest_name && comment.guest_email) {
    return comment.guest_name === guestUserName.value && 
           comment.guest_email === guestUserEmail.value;
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

// Get ticket ID from query params or verify token
onMounted(async () => {
  console.log('ConversationForm mounted');
  console.log('Route query params:', route.query);
  console.log('Route path:', route.path);
  
  // Check if we have a token (from email link)
  const token = route.query.token;
  
  console.log('Token from URL:', token);
  
  if (token) {
    // Verify token and get ticket_id
    loading.value = true;
    try {
      // Ensure CSRF token exists
      await ensureCSRFToken();
      
      console.log('🔍 Verifying ticket access token...');
      console.log('📧 Token:', token);
      const headers = getHeadersWithCSRF();
      const response = await API.post(API.COMMENT_TOKEN_VERIFICATION, { token }, headers);
      console.log('📨 Token verification response:', response);
      
      // La respuesta puede venir como array o como objeto
      const responseData = Array.isArray(response) ? response[0] : response;
      console.log('📦 Response data:', responseData);
      
      const verifiedTicketId = responseData?.ticket_id;
      
      if (verifiedTicketId) {
        console.log('✅ Token verified, ticket_id:', verifiedTicketId);
        ticketId.value = verifiedTicketId;
        await loadConversation();
      } else {
        console.error('❌ No ticket_id in response:', responseData);
        error.value = 'Invalid or expired token';
      }
    } catch (err) {
      console.error('❌ Error verifying token:', err);
      console.error('📋 Error details:', err.message);
      error.value = err?.message || 'Failed to verify access token';
    } finally {
      loading.value = false;
    }
  } else {
    // Normal flow: get ticket ID directly from query params
    console.log('No token, trying direct ID from query');
    ticketId.value = route.query.id;
    if (ticketId.value) {
      console.log('Loading conversation with ID:', ticketId.value);
      loadConversation();
    } else {
      console.error('No ticket ID or token provided');
      error.value = 'No ticket ID or access token provided';
    }
  }
  
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

// Watch for changes in ticket ID or token
watch(() => [route.query.id, route.query.token], async ([newId, newToken]) => {
  if (newToken) {
    // If token changes, verify it
    loading.value = true;
    try {
      console.log('Token changed, verifying...');
      const response = await API.post(API.COMMENT_TOKEN_VERIFICATION, { token: newToken });
      const verifiedTicketId = response?.ticket_id;
      
      if (verifiedTicketId && verifiedTicketId !== ticketId.value) {
        ticketId.value = verifiedTicketId;
        await loadConversation();
      }
    } catch (err) {
      console.error('Error verifying token:', err);
      error.value = err?.message || 'Failed to verify access token';
    } finally {
      loading.value = false;
    }
  } else if (newId && newId !== ticketId.value) {
    // Normal flow: ticket ID changed directly
    ticketId.value = newId;
    loadConversation();
  }
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
</script>

<style scoped>
.conversation-form {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  background: #f3f4f6;
  min-height: 100vh;
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
  font-size: 4rem;
  color: #9ca3af;
  margin-bottom: 16px;
}

.error-text {
  color: #ef4444;
  margin-bottom: 16px;
}

.ticket-header {
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.ticket-header h2 {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  flex: 1;
  line-height: 1.3;
}

.ticket-badges {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.header-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
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
  box-shadow: 0 4px 6px -1px rgba(245, 124, 0, 0.1), 0 2px 4px -1px rgba(245, 124, 0, 0.06);
}

.message-header {
  margin-bottom: 16px;
}

.user-info {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.avatar-icon {
  font-size: 3rem;
  color: #f57c00;
  flex-shrink: 0;
}

.user-details {
  flex: 1;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.user-name-row strong {
  font-size: 1.1rem;
  color: #1f2937;
}

.badge-original {
  display: inline-block;
  background: #f57c00;
  color: white;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.message-date {
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 500;
}

.message-content {
  margin-bottom: 20px;
  padding-left: 60px;
  color: #374151;
  line-height: 1.7;
  font-size: 1rem;
}

.message-content p {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Ticket Metadata Grid */
.ticket-metadata {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
  padding-left: 60px;
}

.metadata-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  border: 1px solid rgba(245, 124, 0, 0.3);
}

.metadata-item ion-icon {
  font-size: 1.4rem;
  color: #f57c00;
  flex-shrink: 0;
  margin-top: 2px;
}

.metadata-item > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.metadata-label {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.metadata-value {
  font-size: 0.95rem;
  color: #1f2937;
  font-weight: 500;
  word-wrap: break-word;
}

/* Attachments in ticket */
.ticket-attachments {
  padding-left: 60px;
}

.attachments-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #374151;
  font-size: 1rem;
}

.attachments-header ion-icon {
  font-size: 1.3rem;
  color: #f57c00;
}

.attachments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.attachment-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  text-decoration: none;
  color: #fdaf66;
  transition: all 0.2s ease;
  cursor: pointer;
}

.attachment-card:hover {
  background: #f9fafb;
  border-color: #f57c00;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.attachment-icon {
  font-size: 2rem;
  color: #f57c00;
  flex-shrink: 0;
}

.attachment-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.attachment-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-date {
  font-size: 0.75rem;
  color: #9ca3af;
}

.conversation-divider {
  text-align: center;
  margin: 40px 0;
  color: #9ca3af;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
  position: relative;
}

.conversation-divider span {
  background: #f3f4f6;
  padding: 0 20px;
  position: relative;
  z-index: 0;
}

.conversation-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(to right, transparent, #d1d5db 20%, #d1d5db 80%, transparent);
  z-index: 0;
}

/* Comments Section */
.comments-section {
  margin-bottom: 32px;
}

.no-comments {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  text-align: center;
  color: #9ca3af;
  background: #f9fafb;
  border-radius: 12px;
  border: 2px dashed #e5e7eb;
}

.no-comments .empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  color: #d1d5db;
}

.no-comments p {
  font-size: 1.1rem;
  margin: 0;
}

.comments-cascade {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Chat Bubbles */
.comment-bubble {
  display: flex;
  flex-direction: column;
  max-width: 75%;
  animation: fadeInUp 0.3s ease;
}

/* Other user comments (left side - gray) */
.comment-other-user {
  align-self: flex-start;
}

.comment-other-user .bubble-header {
  justify-content: flex-start;
}

.comment-other-user .bubble-content {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 18px 18px 18px 4px;
}

/* Current user comments (right side - orange) */
.comment-current-user {
  align-self: flex-end;
}

.comment-current-user .bubble-header {
  justify-content: flex-end;
}

.comment-current-user .bubble-content {
  background: linear-gradient(135deg, #f57c00, #ef6c00);
  color: white;
  border-radius: 18px 18px 4px 18px;
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 0 4px;
}

.bubble-avatar {
  font-size: 1.8rem;
  color: #6b7280;
  flex-shrink: 0;
}

.comment-current-user .bubble-avatar {
  color: #f57c00;
}

.bubble-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bubble-user-name {
  font-size: 0.9rem;
  color: #1f2937;
  font-weight: 600;
}

.comment-current-user .bubble-user-name {
  color: #ef6c00;
}

.bubble-date {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 500;
}

.bubble-content {
  padding: 12px 16px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.bubble-content p {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.5;
  font-size: 0.95rem;
}

.comment-other-user .bubble-content p {
  color: #374151;
}

.comment-current-user .bubble-content p {
  color: white;
}

/* Bubble attachments */
.bubble-attachments {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.comment-current-user .bubble-attachments {
  background: rgba(245, 124, 0, 0.1);
  border-color: rgba(245, 124, 0, 0.3);
}

.bubble-attachments-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 600;
  margin-bottom: 6px;
}

.bubble-attachments-header ion-icon {
  font-size: 1rem;
}

.bubble-attachments-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bubble-attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  text-decoration: none;
  color: #f57c00;
  font-size: 0.85rem;
  transition: all 0.2s ease;
}

.bubble-attachment-item:hover {
  background: #f3f4f6;
  border-color: #f57c00;
  transform: translateX(2px);
}

.bubble-attachment-item ion-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.bubble-attachment-item span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.comment-input-section {
  background: white;
  border-top: 2px solid #f57c00;
  border-radius: 12px;
  padding: 20px;
  margin-top: 32px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.05);
}

.comment-textarea {
  width: 100%;
  margin-bottom: 12px;
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 80px;
  transition: all 0.2s ease;
}

.comment-textarea:focus {
  outline: none;
  background: white;
  border-color: #f57c00;
  box-shadow: 0 0 0 3px rgba(245, 124, 0, 0.1);
}

/* Compact file preview and actions */
.file-preview-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 0.85rem;
}

.file-preview-compact ion-icon {
  font-size: 1.2rem;
  color: #f57c00;
  flex-shrink: 0;
}

.file-preview-compact .file-name {
  flex: 1;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-preview-compact .file-size {
  color: #6b7280;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.file-error-compact {
  color: #ef4444;
  font-size: 0.85rem;
  padding: 8px 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  margin-bottom: 12px;
}

.hidden-input {
  display: none;
}

.comment-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.send-button {
  flex: 1;
  min-width: 120px;
}

.resolve-button {
  flex-shrink: 0;
  min-width: 120px;
}

.error-line {
  color: #ef4444;
  font-size: 0.875rem;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #fef2f2;
  border-radius: 6px;
  border-left: 4px solid #ef4444;
}

.success-line {
  color: #10b981;
  font-size: 0.875rem;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #f0fdf4;
  border-radius: 6px;
  border-left: 4px solid #10b981;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .conversation-form {
    padding: 12px;
    min-height: 100vh;
  }

  .header-top {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .ticket-header h2 {
    font-size: 1.4rem;
    line-height: 1.3;
  }

  .ticket-badges {
    align-self: flex-start;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }

  .header-subtitle {
    font-size: 0.85rem;
  }

  .original-ticket {
    padding: 16px;
    border-radius: 12px;
  }

  .message-content {
    padding-left: 0;
    font-size: 0.95rem;
  }

  /* Ticket metadata grid - stack on mobile */
  .ticket-metadata {
    grid-template-columns: 1fr;
    padding-left: 0;
    gap: 10px;
  }

  .metadata-item {
    padding: 10px;
  }

  .metadata-item ion-icon {
    font-size: 1.2rem;
  }

  /* Attachments in ticket */
  .ticket-attachments {
    padding-left: 0;
  }

  .attachments-grid {
    grid-template-columns: 1fr;
  }

  .attachment-card {
    padding: 10px;
  }

  /* Conversation divider */
  .conversation-divider {
    margin: 30px 0;
    font-size: 0.8rem;
  }

  /* Chat bubbles responsive */
  .comment-bubble {
    max-width: 90%;
  }

  .bubble-avatar {
    font-size: 1.6rem;
  }

  .bubble-user-name {
    font-size: 0.85rem;
  }

  .bubble-date {
    font-size: 0.7rem;
  }

  .bubble-content {
    padding: 10px 12px;
  }

  .bubble-content p {
    font-size: 0.9rem;
  }

  /* Comment input section */
  .comment-input-section {
    padding: 12px;
    margin-top: 20px;
    border-radius: 12px;
  }

  .comment-textarea {
    font-size: 0.95rem;
    min-height: 70px;
  }

  .comment-actions {
    flex-direction: column;
    gap: 8px;
  }

  .comment-actions ion-button {
    width: 100%;
    margin: 0;
  }

  .send-button,
  .resolve-button {
    min-width: 100%;
    flex: 1 1 100%;
  }

  /* File preview on mobile */
  .file-preview-compact {
    flex-wrap: wrap;
    padding: 10px;
  }

  .file-preview-compact .file-name {
    max-width: 100%;
  }

  /* Empty state */
  .no-comments {
    padding: 40px 16px;
  }

  .no-comments .empty-icon {
    font-size: 3rem;
  }

  .no-comments p {
    font-size: 1rem;
  }
}

/* Tablet breakpoint */
@media (max-width: 1024px) and (min-width: 769px) {
  .conversation-form {
    padding: 18px;
  }

  .ticket-metadata {
    grid-template-columns: repeat(2, 1fr);
  }

  .comment-bubble {
    max-width: 80%;
  }
}

/* Small mobile devices */
@media (max-width: 480px) {
  .conversation-form {
    padding: 8px;
  }

  .ticket-header h2 {
    font-size: 1.2rem;
  }

  .header-subtitle {
    font-size: 0.8rem;
  }

  .original-ticket {
    padding: 12px;
  }

  .metadata-item {
    padding: 8px;
  }

  .comment-bubble {
    max-width: 95%;
  }

  .bubble-avatar {
    font-size: 1.4rem;
  }

  .bubble-content {
    padding: 8px 10px;
  }

  .comment-input-section {
    padding: 10px;
  }

  .comment-textarea {
    min-height: 60px;
    font-size: 0.9rem;
  }
}
</style>
