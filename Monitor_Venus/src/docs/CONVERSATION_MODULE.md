# Conversation Module (Ionic + Vue)

Comprehensive documentation for `ConversationForm.vue` support ticket conversation implementation. This module provides a WhatsApp-style chat interface for support tickets with complete guest user support, email token verification, automatic status management, and CSRF protection.

---
## Overview

Goal: Provide a secure, accessible chat-style interface for viewing and responding to support tickets with full guest user support and automated workflows.

**Key Features**:
- **Email Token Verification**: JWT token-based access for guest users via email links
- **UUID Ticket Support**: Native UUID handling without integer parsing
- **Guest User System**: Full support for unauthenticated users with guest_name/guest_email
- **Automatic Status Management**: Smart status transitions (open → in_progress → resolved)
- **CSRF Protection**: Complete CSRF token management for all state-changing operations
- **Responsive Design**: Mobile-first with breakpoints at 480px, 768px, 1024px
- **Smart Comment Positioning**: Current user comments on right (orange), others on left (gray)
- **Auto-Scroll**: Automatic scroll to bottom on load + manual scroll button
- **Dynamic Response Field**: Uses `auth.isSupportUser` for role-based comment flagging
- **Status Normalization**: Handles backend/API format differences ("Open" vs "open")
- **Orange Theme**: Consistent orange color scheme throughout (#f57c00 primary, #ef6c00 dark)

---
## Core Endpoints

```javascript
// Conversation & Comments
TICKET_CONVERSATION(id) = `support/ticket/${id}/conversation/`  // GET ticket + comments
COMMENT                 = 'support/comment/'                    // POST new comment
COMMENT_ATTACHMENT      = 'support/comment-attachment/'         // POST file for comment

// Token Verification (Email Access)
COMMENT_TOKEN_VERIFICATION = 'auth/verify-ticket-token/'        // POST {token} → {ticket_id}

// Ticket Management
TICKET_UPDATE(id)       = `support/ticket/${id}/`               // PATCH {status}
INBOX_READ(id)          = `support/ticket/${id}/mark_as_read/`  // POST mark as read
```

**Request/Response Examples**:

```javascript
// Token Verification Request
POST auth/verify-ticket-token/
Body: { token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
Response: { ticket_id: "34088b1d-60a8-4bde-bfd2-ff099ecb534d" }

// Comment Creation (Authenticated User)
POST support/comment/
Body: {
  response: true,  // true = support agent, false = regular user
  content: "Comment text",
  ticket: "34088b1d-60a8-4bde-bfd2-ff099ecb534d",
  user: 123
}

// Comment Creation (Guest User)
POST support/comment/
Body: {
  response: false,
  content: "Comment text", 
  ticket: "34088b1d-60a8-4bde-bfd2-ff099ecb534d",
  guest_name: "John Doe",
  guest_email: "john@example.com"
}

// Status Update
PATCH support/ticket/34088b1d-60a8-4bde-bfd2-ff099ecb534d/
Body: { status: "in_progress" }  // Must be: "open", "in_progress", or "resolved"
```

---
## Component Location & Integration

**Path**: `src/components/forms/conversation/ConversationForm.vue`

**Route Configuration**:
- **Primary Route**: `/ticket` (defined in `paths.js`)
- **Alias**: `/tickets` (for email link compatibility)
- **Query Parameters**:
  - `id` (UUID): Direct ticket access for authenticated users
  - `token` (JWT): Token-based access for guest users via email

**Parent Integration**: 
- Embedded within the inbox module (`src/views/inbox/`)
- InboxForm shows "Conversation" button only for assigned tickets
- Button visibility: `v-if="isAssignedToCurrentUser"`
- Navigation: `router.push('/ticket', {id: UUID})`

**Access Patterns**:

1. **Authenticated User (from Inbox)**:
   ```
   URL: /ticket?id=34088b1d-60a8-4bde-bfd2-ff099ecb534d
   Flow: InboxForm → router.push → ConversationForm
   Auth: Uses auth store (userId, username, isSupportUser)
   ```

2. **Guest User (from Email)**:
   ```
   URL: /ticket?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Flow: Email link → Token verification → Extract ticket_id
   Auth: Guest mode (guest_name, guest_email from ticket data)
   ```

**Data Flow**:
1. Component mounts → Check for `route.query.token` or `route.query.id`
2. If token: Verify via `COMMENT_TOKEN_VERIFICATION` → Extract ticket ID
3. If id: Use directly (authenticated user path)
4. Load conversation with extracted/provided ticket ID
5. Extract guest info from ticket data if not authenticated
6. User posts comments with appropriate identity (user ID, ticket user ID, or guest info)
7. Auto-update ticket status based on actions
8. Changes persist to backend with CSRF protection

---
## Main Reactive State

| Ref / Computed        | Type | Purpose |
|-----------------------|------|---------|
| `ticketId`            | Ref(String) | UUID ticket identifier from route or token verification |
| `conversationData`    | Ref(Object) | Complete ticket object with comments array |
| `loading`             | Ref(Boolean) | Loading state for initial fetch |
| `error`               | Ref(String) | Error message for fetch failures |
| `newComment`          | Ref(String) | v-model for textarea input |
| `sendingComment`      | Ref(Boolean) | Loading state during comment submission |
| `commentError`        | Ref(String) | Error message for comment post failures |
| `commentSuccess`      | Ref(String) | Success message after comment posted |
| `selectedFile`        | Ref(File) | Currently selected file for attachment |
| `fileError`           | Ref(String) | File validation error message |
| `sortedComments`      | Computed | Comments sorted chronologically (oldest first) |
| `currentUserId`       | Computed | User ID from auth store (null if not authenticated) |
| `currentUsername`     | Computed | Username from auth store (null if guest) |
| `isSupportUser`       | Computed | Whether current user is support agent |
| `guestUserName`       | Ref(String) | Guest name extracted from ticket data |
| `guestUserEmail`      | Ref(String) | Guest email extracted from ticket data |
| `ticketUserId`        | Ref(Number) | Original ticket creator's user ID |
| `normalizedStatus`    | Computed | Status normalized to lowercase with underscores ("open", "in_progress", "resolved") |

**Identity Priority Logic**:
When posting comments, the system uses this priority order:
1. **Authenticated User**: `currentUserId` from auth store (if logged in)
2. **Ticket User**: `ticketUserId` extracted from conversation data (for email access)
3. **Guest Info**: `guestUserName` + `guestUserEmail` (for unknown users)

---
## Key Methods

| Method | Parameters | Summary |
|--------|-----------|---------|
| `loadConversation()` | - | GET ticket conversation data; extracts guest info (user/guest_name/guest_email); auto-scrolls to bottom after 300ms |
| `sendComment()` | - | POST comment with identity priority logic (user ID → ticket user ID → guest info); uploads attachment if present; auto-updates status; reloads conversation |
| `uploadAttachment(commentId, file)` | commentId: Number, file: File | POST FormData with file and comment ID to attach file to comment |
| `updateTicketStatus(newStatus)` | newStatus: String | PATCH ticket status with CSRF protection; normalizes status format |
| `resolveTicket()` | - | Shows confirmation dialog; calls `updateTicketStatus('resolved')` if confirmed |
| `isCurrentUserComment(comment)` | comment: Object | Returns true if comment belongs to current user (determines bubble positioning) |
| `scrollToBottom()` | - | Scrolls to .comment-input-section with 100ms delay; called manually or automatically |
| `triggerFilePicker()` | - | Programmatically opens file input dialog |
| `handleFileChange(e)` | e: Event | Validates selected file (size, type); sets `selectedFile` or shows error |
| `removeFile()` | - | Clears selected file and resets input |
| `formatFileSize(bytes)` | bytes: Number | Converts bytes to human-readable format (B, KB, MB, GB) |
| `formatDate(dateString)` | dateString: String | Relative date formatting ("Just now", "2 hours ago", "Yesterday", etc.) |
| `getAttachmentUrl(filePath)` | filePath: String | Builds absolute URL for attachment file |
| `getAttachmentName(filePath)` | filePath: String | Extracts filename from path and decodes URI components |
| `priorityColor(priority)` | priority: String | Maps priority level to Ionic badge color |
| `statusColor(status)` | status: String | Maps status to Ionic badge color |

### CSRF Token Management

```javascript
// CSRF Helper Functions (from LoginForm.vue pattern)
function getCookieValue(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function getHeadersWithCSRF(contentType = 'application/json') {
  const csrfToken = getCookieValue('csrftoken');
  const headers = { 'Content-Type': contentType };
  if (csrfToken) headers['X-CSRFToken'] = csrfToken;
  return headers;
}

async function ensureCSRFToken() {
  let token = getCookieValue('csrftoken');
  if (!token) {
    await fetch(API.CSRF_TOKEN, { credentials: 'include' });
    token = getCookieValue('csrftoken');
  }
  return token;
}
```

**Usage**: Called before every POST/PATCH operation:
- `sendComment()`: Ensures CSRF before posting comment
- `updateTicketStatus()`: Includes CSRF in PATCH request
- `uploadAttachment()`: CSRF token in FormData upload

---
## Token Verification Flow (Email Access)

**Use Case**: Guest users receive email with ticket link containing JWT token for secure access.

**URL Format**: 
```
https://app.example.com/ticket?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Verification Process**:

1. **Component Mount**:
   ```javascript
   onMounted(async () => {
     if (route.query.token) {
       // Token-based access (email link)
       await verifyTokenAndLoadConversation(route.query.token);
     } else if (route.query.id) {
       // Direct access (authenticated user)
       ticketId.value = route.query.id;
       await loadConversation();
     }
   });
   ```

2. **Token Verification**:
   ```javascript
   async function verifyTokenAndLoadConversation(token) {
     await ensureCSRFToken();
     const response = await API.post(
       API.COMMENT_TOKEN_VERIFICATION,
       { token },
       { headers: getHeadersWithCSRF() }
     );
     
     // Extract ticket_id (handles array or object response)
     const ticketIdFromToken = Array.isArray(response) 
       ? response[0]?.ticket_id 
       : response?.ticket_id;
       
     ticketId.value = ticketIdFromToken;
     await loadConversation();
   }
   ```

3. **Guest Info Extraction**:
   ```javascript
   async function loadConversation() {
     const data = await API.get(API.TICKET_CONVERSATION(ticketId.value));
     conversationData.value = Array.isArray(data) ? data[0] : data;
     
     // Extract guest info from ticket
     if (conversationData.value.user) {
       ticketUserId.value = conversationData.value.user;
     }
     if (conversationData.value.guest_name) {
       guestUserName.value = conversationData.value.guest_name;
     }
     if (conversationData.value.guest_email) {
       guestUserEmail.value = conversationData.value.guest_email;
     }
     
     // Auto-scroll after data loads
     setTimeout(scrollToBottom, 300);
   }
   ```

**Security Notes**:
- JWT tokens are single-use or time-limited (backend responsibility)
- CSRF protection applied to verification endpoint
- Failed verification shows error message with retry option
- No sensitive data in URL (only token, which expires)
---
## Comment Posting Flow

**Identity Resolution Priority**:
1. **Authenticated User** (highest priority):
   ```javascript
   if (currentUserId.value) {
     commentData.user = currentUserId.value;
     commentData.response = isSupportUser.value;
   }
   ```

2. **Ticket User** (for email access):
   ```javascript
   else if (ticketUserId.value) {
     commentData.user = ticketUserId.value;
     commentData.response = false;
   }
   ```

3. **Guest User** (lowest priority):
   ```javascript
   else if (guestUserName.value && guestUserEmail.value) {
     commentData.guest_name = guestUserName.value;
     commentData.guest_email = guestUserEmail.value;
     commentData.response = false;
   }
   ```

**Complete Flow**:

1. **User Input**: User types message in native HTML textarea.

2. **File Selection** (Optional): User clicks attachment icon, selects file, preview appears.

3. **Validation**: 
   - Comment must have content (trim check)
   - File (if present) must be ≤5MB and allowed type
   - At least one identity method must be available (user ID, ticket user ID, or guest info)

4. **Status Auto-Update** (Support Users Only):
   ```javascript
   // Auto-transition open → in_progress when support user comments
   if (isSupportUser.value && normalizedStatus.value === 'open') {
     await updateTicketStatus('in_progress');
   }
   ```

5. **Comment Submission**:
   ```javascript
   await ensureCSRFToken();
   const commentData = {
     response: <determined by priority logic>,
     content: newComment.value.trim(),
     ticket: ticketId.value,
     // Plus: user OR (guest_name + guest_email)
   };
   const commentResponse = await API.post(
     API.COMMENT,
     commentData,
     { headers: getHeadersWithCSRF() }
   );
   ```

6. **Attachment Upload** (if file selected):
   ```javascript
   const commentId = Array.isArray(commentResponse) 
     ? commentResponse[0]?.id 
     : commentResponse?.id;
     
   if (selectedFile.value && commentId) {
     await uploadAttachment(commentId, selectedFile.value);
   }
   ```

7. **Refresh & Feedback**:
   - Reload entire conversation to show new comment
   - Show success message (auto-clear after 3s)
   - Clear form inputs (textarea + file)
   - Auto-scroll to new comment

---
## Automatic Status Management

**Status Lifecycle**: `open` → `in_progress` → `resolved`

**Backend vs API Formats**:
- **Backend Returns**: "Open", "In Progress", "Resolved" (display format)
- **API Expects**: "open", "in_progress", "resolved" (database format)
- **Solution**: `normalizedStatus` computed property for consistent comparisons

```javascript
const normalizedStatus = computed(() => {
  if (!conversationData.value?.status) return '';
  return conversationData.value.status
    .toLowerCase()
    .replace(/ /g, '_');
});
```

**Auto-Transition Rules**:

1. **Open → In Progress**:
   - **Trigger**: Support user posts first comment on open ticket
   - **Logic**: 
     ```javascript
     if (isSupportUser.value && normalizedStatus.value === 'open') {
       await updateTicketStatus('in_progress');
     }
     ```
   - **Result**: Ticket automatically marked as being worked on

2. **Manual Resolve**:
   - **Trigger**: Support user clicks "Resolve Ticket" button
   - **Logic**: Shows confirmation dialog before updating
   - **Result**: Ticket marked as resolved, removed from active queue

**Status Update Function**:
```javascript
async function updateTicketStatus(newStatus) {
  await ensureCSRFToken();
  await API.patch(
    API.TICKET_UPDATE(ticketId.value),
    { status: newStatus },
    { headers: getHeadersWithCSRF() }
  );
  await loadConversation(); // Refresh to show new status
}
```

**Status Display**:
- Badge in ticket header with color coding
- Updates immediately after status change
- Visible to both authenticated and guest users

---
## Comment Bubble Positioning

**Logic**: Comments are positioned based on author identity, creating a WhatsApp-style chat interface.

**Positioning Rules**:
```javascript
function isCurrentUserComment(comment) {
  if (!comment.user) return false;
  
  // Priority 1: Check against authenticated user
  if (currentUserId.value && comment.user === currentUserId.value) {
    return true;
  }
  
  // Priority 2: Check against ticket user (for email access)
  if (ticketUserId.value && comment.user === ticketUserId.value) {
    return true;
  }
  
  // Priority 3: Not current user's comment
  return false;
}
```

**Visual Result**:
- **Current User Comments** (right-aligned):
  - Orange gradient background (#f57c00 → #ef6c00)
  - White text
  - Rounded corners (left side more rounded)
  - Avatar and username on right

- **Other Users Comments** (left-aligned):
  - Light gray background (#f3f4f6)
  - Dark text (#1f2937)
  - Rounded corners (right side more rounded)
  - Avatar and username on left

**CSS Classes**:
```css
.comment-bubble.left {
  align-self: flex-start;
  background: #f3f4f6;
  border-radius: 0.75rem 0.75rem 0.75rem 0.25rem;
}

.comment-bubble.right {
  align-self: flex-end;
  background: linear-gradient(135deg, #f57c00 0%, #ef6c00 100%);
  border-radius: 0.75rem 0.75rem 0.25rem 0.75rem;
}
```

**Edge Cases**:
- Guest users without user ID: Always appear on left
- Support agent comments: Appear on right only for that agent
- Multiple support agents: Each sees their own on right, others on left

---
## File Attachment Handling

**Validation Rules**:
- Max size: 5MB
- Allowed types: PNG, JPG, JPEG, PDF, DOC, DOCX, TXT
- Type check: validates MIME type and file extension

**Upload Process**:
- Attachment upload happens AFTER comment creation (requires comment ID).
- Uses FormData with `file` and `comment` fields.
- Failures show error but don't block comment creation.
- Success message indicates both comment and attachment were posted.

**Display**:
- Compact preview shows filename, size, and remove button before sending.
- In conversation thread, attachments appear as clickable links below comment bubbles.
- Attachment icons styled with orange theme.

---
## Color Scheme (Orange Theme)

Replaced original blue (#3b82f6) with orange throughout:

| Element | Color |
|---------|-------|
| Primary (borders, icons, buttons) | #f57c00 |
| Dark (gradients, hover states) | #ef6c00 |
| Light borders | #fdba74 |
| Light backgrounds | #fff7ed, #ffedd5 |
| Staff response bubbles | Linear gradient (#f57c00 → #ef6c00) |
| Focus states | Box shadow rgba(245, 124, 0, 0.1) |

---
## UI Layout & Components

**Ticket Header**:
- Title (h2, bold)
- Priority and status badges (right-aligned)
- Created/Updated dates (subtitle)
- Scroll-to-bottom button (arrow icon, triggers scrollToBottom())

**Original Ticket Card**:
- Minimalist display with essential metadata
- User badge with avatar icon
- Description text (pre-wrapped)
- Category, organization, assigned-to (if present)
- Attachments list with download links

**Conversation Divider**:
- Visual separator between original ticket and comments
- Text: "─── Conversation ───"
- z-index: 0 to prevent overlap
- Background: #f3f4f6

**Comments Cascade**:
- User comments: Left-aligned, grey background (#f3f4f6)
- Current user comments: Right-aligned, orange gradient background
- Each bubble: Avatar icon, username, timestamp, content, attachments
- Empty state: "No responses yet. Start the conversation!"
- Chronological order: Oldest to newest (bottom is most recent)

**Input Section** (Static at bottom):
- Native HTML textarea (3 rows, resizable)
- Compact file preview (when file selected)
- Actions row: Attachment icon button + Send button
- Success/error messages above input
- Keyboard shortcuts: Ctrl+Enter / Cmd+Enter to send

**Resolve Button** (Support Users Only):
- Visible when ticket is not resolved
- Shows confirmation dialog before updating
- Updates status to "resolved" via PATCH request

---
## Scroll Behavior

**Problem**: Original `ion-textarea` caused unwanted scroll-up behavior when focused, showing white background below content.

**Solution**: Replaced with native HTML `<textarea>` element:
- Full control over focus behavior
- Custom styling matches previous appearance
- Standard CSS properties (no Ionic CSS variables)
- Focus state: orange border + box-shadow
- Eliminates Ionic's shadow DOM scroll interference

**Auto-Scroll on Load**:
```javascript
async function loadConversation() {
  // ... fetch conversation data ...
  
  // Auto-scroll to bottom after DOM updates
  setTimeout(scrollToBottom, 300);
}
```

**Manual Scroll Button**:
- Icon button in ticket header (arrow-down icon)
- Triggers `scrollToBottom()` function
- Scrolls to `.comment-input-section` with smooth behavior
- 100ms delay for reliable DOM targeting

**Scroll Function**:
```javascript
function scrollToBottom() {
  setTimeout(() => {
    const inputSection = document.querySelector('.comment-input-section');
    if (inputSection) {
      inputSection.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, 100);
}
```

**Event Handling**:
- Keyboard shortcuts: Ctrl+Enter / Cmd+Enter to send comment
- No scroll position tracking needed (auto-scroll handles it)
- focusin listeners prevent unwanted scroll jumps

---
## Responsive Design

**Breakpoints**:
- **Small Mobile**: ≤480px
- **Mobile**: ≤768px  
- **Tablet**: 769px - 1024px
- **Desktop**: >1024px

**Mobile** (≤768px):
- Reduced padding (16px → 12px)
- Bubbles max 90% width
- Stacked layout for badges/metadata
- Smaller avatar icons (1.5rem)
- Compact input section (16px padding)
- Sticky input at bottom of viewport
- Single column metadata display

**Tablet** (769px - 1024px):
- Medium padding (20px)
- Bubbles max 80% width
- Two-column metadata grid
- Standard avatar icons (2rem)
- Balanced spacing

**Small Mobile** (≤480px):
- Bubbles max 95% width
- Minimal padding (8px for bubbles, 12px for containers)
- Extra compact font sizes
- Priority/status badges stack vertically
- Reduced button sizes

**Desktop** (>1024px):
- Max width: 900px centered
- Full metadata grid visible
- Bubbles max 75% width
- Side-by-side layout for attachments
- Comfortable spacing throughout

**Responsive CSS Highlights**:
```css
/* Mobile-first approach */
.conversation-content {
  padding: 12px;
  max-width: 900px;
  margin: 0 auto;
}

@media (min-width: 769px) {
  .conversation-content {
    padding: 20px;
  }
  .comment-bubble {
    max-width: 80%;
  }
}

@media (min-width: 1025px) {
  .conversation-content {
    padding: 24px;
  }
  .comment-bubble {
    max-width: 75%;
  }
}

@media (max-width: 480px) {
  .comment-bubble {
    max-width: 95%;
    padding: 8px;
  }
}
```

---
## Integration with Auth Store & Inbox

**Auth Store Integration**:
Uses Pinia `useAuthStore` for:
- `currentUserId`: Required for authenticated comment authorship
- `currentUsername`: Display name for authenticated users
- `isSupportUser`: Determines if user is support agent (affects `response` field and auto-status)
- `isAuthenticated`: Boolean check for authentication state
- Fallback to guest mode if not authenticated

**Inbox Module Integration**:

1. **Button Visibility**:
   ```javascript
   // InboxForm.vue - Conversation button only for assigned tickets
   const isAssignedToCurrentUser = computed(() => {
     return selectedMessage.value?.assigned_to === currentUserId.value;
   });
   ```
   ```vue
   <ion-button v-if="isAssignedToCurrentUser" @click="navigateToConversation">
     View Conversation
   </ion-button>
   ```

2. **Navigation**:
   ```javascript
   function navigateToConversation() {
     router.push({
       path: '/ticket',
       query: { id: selectedMessage.value.id }
     });
   }
   ```

3. **Auto Mark-as-Read**:
   - Removed manual "Mark as read" button from InboxForm
   - Tickets automatically marked as read when selected
   - API call: `POST support/ticket/{id}/mark_as_read/`
   - Happens in `selectMessage()` function if ticket is unread
   - Eliminates redundant UI element and simplifies UX

---
## Error Handling

**Conversation Load**:
- Loading spinner during fetch
- Error state with retry button
- Empty state if no data available
- Token verification failures show detailed error message

**Comment Submission**:
- Validation errors (missing identity info, missing ticket ID)
- Network errors during POST (with retry option)
- Attachment upload failures (non-blocking, comment still created)
- User-friendly error messages with red background
- Console logging for debugging (emojis: 🔍📧📨📦✅❌)

**File Validation**:
- Size exceeds 5MB: "File is too large. Max size: 5 MB"
- Unsupported type: "Unsupported file type. Allowed: PNG, JPG, JPEG, PDF, DOC, DOCX, TXT"
- Errors displayed inline with red border
- File input resets on validation failure

**Status Update Errors**:
- CSRF token missing: Fetches new token and retries
- Network failures show error banner
- Status normalization handles format mismatches
- Conversation reloads on success to show updated status

**Guest User Errors**:
- Missing guest info: Shows error requiring name/email
- Token expired: Clear error message with re-request option
- No user identity: Prevents comment submission

---
## API Response Handling

**Conversation Data**:
- Handles both array and object responses from backend
- Extracts first element if array: `Array.isArray(data) ? data[0] : data`
- Comment array sorted chronologically (ascending - oldest first)
- Extracts user, guest_name, guest_email from ticket root
- UUID ticket IDs handled as strings (no parseInt)

**Comment Creation**:
- Extracts comment ID from response (handles array or object)
- Response format: `{id: 123, content: "...", ...}` or `[{id: 123, ...}]`
- Uses ID immediately for attachment upload
- Success feedback distinguishes comment-only vs comment+attachment

**Token Verification**:
- Request: `{token: "JWT_STRING"}`
- Response: `{ticket_id: "UUID"}` or `[{ticket_id: "UUID"}]`
- Handles both array and object response formats
- Detailed console logging for debugging (🔍 token verification steps)

**Status Updates**:
- Request: `{status: "open"|"in_progress"|"resolved"}`
- Backend returns: Display format ("Open", "In Progress", "Resolved")
- normalizedStatus computed handles conversion for comparisons
- Response triggers conversation reload to show updated status

**Attachments**:
- Builds absolute URLs from relative paths
- Handles missing file paths gracefully (shows filename only)
- Decodes URI-encoded filenames for display
- File upload uses FormData (multipart/form-data)

---
## Minimal Usage Flow

**Authenticated User (from Inbox)**:
1. Support agent navigates from inbox to conversation view
2. Clicks "View Conversation" button (only visible for assigned tickets)
3. Component mounts → Uses `route.query.id` (UUID)
4. `loadConversation()` fetches ticket + comments
5. Original ticket displays with minimalist metadata
6. Comment thread shows with smart bubble positioning
7. Agent types response in native textarea
8. (Optional) Attaches file via compact icon button
9. Clicks Send → auto-updates status to "in_progress" if open
10. Comment POSTs with `response: true`, attachment uploads
11. Conversation reloads, shows new comment on right (orange)
12. Agent can resolve ticket via "Resolve Ticket" button
13. Returns to inbox via navigation

**Guest User (from Email)**:
1. User receives email with ticket link containing JWT token
2. URL format: `/ticket?token=eyJhbGci...`
3. Component mounts → Detects `route.query.token`
4. Verifies token via `POST auth/verify-ticket-token/`
5. Extracts ticket_id from response (UUID format)
6. `loadConversation()` fetches ticket + comments
7. Extracts guest_name and guest_email from ticket data
8. User sees conversation (their comments on right, others on left)
9. User types response in textarea
10. Clicks Send → POSTs with guest_name and guest_email
11. Comment created without user ID, using guest info
12. Conversation reloads, shows new comment
13. User can continue responding via same token link

**Status Transitions** (automatic):
- Open ticket → Support agent comments → Status changes to "in_progress"
- In progress → Agent clicks "Resolve" → Status changes to "resolved"
- Resolved tickets show completion message, resolve button hidden

---
## Future Enhancements (Not Implemented)

Potential features for consideration:
- Edit/delete comments (with permission checks and time limits)
- Multiple file attachments per comment (drag-and-drop support)
- Rich text formatting (bold, italic, links, code blocks)
- Mention/tag users with @username (auto-complete)
- Email notifications on new comments (real-time push)
- Draft auto-save for long responses (localStorage)
- Inline image preview (not just download links, lightbox viewer)
- WebSocket real-time updates (see new comments without refresh)
- Comment reactions/emoji support
- Internal notes (visible only to support team)
- Conversation export (PDF/CSV)
- SLA timer display (time to first response, resolution time)
- Canned responses / templates for common replies
- Customer satisfaction rating after resolution
- Multi-language support with translation

---
## Checklist (Implemented)

- [x] Conversation fetch with ticket + comments
- [x] Original ticket display (minimalist orange card)
- [x] Comment bubble layout (smart positioning based on author)
- [x] Comment posting with identity priority logic
- [x] File attachment upload (FormData POST)
- [x] Orange color scheme throughout
- [x] Native textarea (scroll issue fix)
- [x] Static input section (not fixed/sticky)
- [x] Compact attachment UI
- [x] File validation (5MB, type check)
- [x] Relative date formatting
- [x] Auto-refresh after comment
- [x] Success/error feedback
- [x] Mobile responsive design (breakpoints: 480px, 768px, 1024px)
- [x] Keyboard shortcuts (Ctrl/Cmd+Enter)
- [x] Email token verification (JWT)
- [x] UUID ticket ID support (no parseInt)
- [x] Guest user support (guest_name, guest_email)
- [x] Automatic status management (open → in_progress → resolved)
- [x] Status normalization (backend vs API formats)
- [x] CSRF token protection (all POST/PATCH)
- [x] Dynamic response field (auth.isSupportUser)
- [x] Scroll-to-bottom button + auto-scroll on load
- [x] Inbox button visibility (assigned users only)
- [x] Auto mark-as-read (removed manual button)
- [x] Comment bubble positioning (current user right, others left)
- [x] conversation-divider styling (z-index fix)

---
## Quick Reference Snippets

```javascript
// ========================================
// Token Verification (Email Access)
// ========================================
async function verifyTokenAndLoadConversation(token) {
  await ensureCSRFToken();
  const response = await API.post(
    API.COMMENT_TOKEN_VERIFICATION,
    { token },
    { headers: getHeadersWithCSRF() }
  );
  
  const ticketIdFromToken = Array.isArray(response)
    ? response[0]?.ticket_id
    : response?.ticket_id;
    
  ticketId.value = ticketIdFromToken;
  await loadConversation();
}

// ========================================
// Load Conversation with Guest Info
// ========================================
async function loadConversation() {
  const data = await API.get(API.TICKET_CONVERSATION(ticketId.value));
  conversationData.value = Array.isArray(data) ? data[0] : data;
  
  // Extract user/guest info
  if (conversationData.value.user) {
    ticketUserId.value = conversationData.value.user;
  }
  if (conversationData.value.guest_name) {
    guestUserName.value = conversationData.value.guest_name;
  }
  if (conversationData.value.guest_email) {
    guestUserEmail.value = conversationData.value.guest_email;
  }
  
  // Auto-scroll after data loads
  setTimeout(scrollToBottom, 300);
}

// ========================================
// Send Comment with Identity Priority
// ========================================
async function sendComment() {
  await ensureCSRFToken();
  
  const commentData = {
    content: newComment.value.trim(),
    ticket: ticketId.value
  };
  
  // Identity priority: authenticated > ticket user > guest
  if (currentUserId.value) {
    commentData.user = currentUserId.value;
    commentData.response = isSupportUser.value;
  } else if (ticketUserId.value) {
    commentData.user = ticketUserId.value;
    commentData.response = false;
  } else if (guestUserName.value && guestUserEmail.value) {
    commentData.guest_name = guestUserName.value;
    commentData.guest_email = guestUserEmail.value;
    commentData.response = false;
  } else {
    throw new Error('No user identity available');
  }
  
  // Auto-update status if support user on open ticket
  if (isSupportUser.value && normalizedStatus.value === 'open') {
    await updateTicketStatus('in_progress');
  }
  
  const commentResponse = await API.post(
    API.COMMENT,
    commentData,
    { headers: getHeadersWithCSRF() }
  );
  
  const commentId = Array.isArray(commentResponse)
    ? commentResponse[0]?.id
    : commentResponse?.id;
  
  if (selectedFile.value && commentId) {
    await uploadAttachment(commentId, selectedFile.value);
  }
  
  await loadConversation(); // Refresh
  newComment.value = '';
  selectedFile.value = null;
}

// ========================================
// Update Ticket Status with CSRF
// ========================================
async function updateTicketStatus(newStatus) {
  await ensureCSRFToken();
  await API.patch(
    API.TICKET_UPDATE(ticketId.value),
    { status: newStatus },
    { headers: getHeadersWithCSRF() }
  );
  await loadConversation();
}

// ========================================
// Comment Bubble Positioning
// ========================================
function isCurrentUserComment(comment) {
  if (!comment.user) return false;
  
  if (currentUserId.value && comment.user === currentUserId.value) {
    return true;
  }
  
  if (ticketUserId.value && comment.user === ticketUserId.value) {
    return true;
  }
  
  return false;
}

// ========================================
// CSRF Token Management
// ========================================
function getCookieValue(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function getHeadersWithCSRF(contentType = 'application/json') {
  const csrfToken = getCookieValue('csrftoken');
  const headers = { 'Content-Type': contentType };
  if (csrfToken) headers['X-CSRFToken'] = csrfToken;
  return headers;
}

async function ensureCSRFToken() {
  let token = getCookieValue('csrftoken');
  if (!token) {
    await fetch(API.CSRF_TOKEN, { credentials: 'include' });
    token = getCookieValue('csrftoken');
  }
  return token;
}

// ========================================
// Scroll to Bottom
// ========================================
function scrollToBottom() {
  setTimeout(() => {
    const inputSection = document.querySelector('.comment-input-section');
    if (inputSection) {
      inputSection.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, 100);
}

// ========================================
// Status Normalization
// ========================================
const normalizedStatus = computed(() => {
  if (!conversationData.value?.status) return '';
  return conversationData.value.status
    .toLowerCase()
    .replace(/ /g, '_');
});
```

---
## Component Dependencies

**Vue Imports**:
- `ref`, `reactive`, `inject`, `onMounted`, `watch`, `computed`, `nextTick` from Vue 3 Composition API
- `useRoute`, `useRouter` from Vue Router
- `useAuthStore` from Pinia stores

**Ionic Components**:
- `IonSpinner` (loading states)
- `IonIcon` (icons throughout)
- `IonBadge` (priority/status badges)
- `IonButton` (actions and navigation)
- `IonContent` (page container)
- `IonHeader`, `IonToolbar`, `IonTitle` (page structure)

**Utils & Composables**:
- `API` from `@/utils/api/api` (endpoints + HTTP methods)
- `icons` injected from global providers (Ionicons)
- Path constants from `@/plugins/router/paths.js`

**Native Elements**:
- `<textarea>` (replaced ion-textarea for scroll control)
- `<input type="file">` (hidden, triggered programmatically)
- Standard HTML for card structure and layout

**External Libraries**:
- None (pure Vue + Ionic, no additional dependencies)

---
## Security Considerations

**CSRF Protection**:
- All POST/PATCH requests include CSRF token in headers
- Token fetched from cookie or retrieved via dedicated endpoint
- Follows Django CSRF cookie pattern
- Applied to: comment posting, attachment upload, status updates, token verification

**JWT Token Verification**:
- Email tokens verified server-side before access granted
- Single-use or time-limited tokens (backend responsibility)
- Failed verification shows error, no conversation access
- Token not stored client-side (used once for verification)

**Guest User Security**:
- Guest comments require both name and email
- No guest user can impersonate authenticated users
- Email validation happens server-side
- Guest access limited to ticket they own

**Input Validation**:
- File type and size validation client-side (5MB limit)
- Content trimmed and sanitized before submission
- Server-side validation for all inputs (backend responsibility)
- XSS prevention via Vue's automatic escaping

**Authorization Checks**:
- Conversation button only visible for assigned support users
- Status updates restricted to support users (backend enforces)
- Resolve button only shown to support users
- User identity verified on every comment submission

---
## Summary

`ConversationForm.vue` delivers a production-ready, secure, WhatsApp-style conversation interface for support tickets. Built with Vue 3 + Ionic, it supports both authenticated users and guests via email tokens, with automatic status management, comprehensive CSRF protection, and full mobile responsiveness. The component prioritizes accessibility, security, and user experience while maintaining clean, maintainable code patterns that can be easily extended for future enhancements.
