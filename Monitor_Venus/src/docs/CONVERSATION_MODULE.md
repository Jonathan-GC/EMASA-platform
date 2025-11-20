# Conversation Module (Ionic + Vue)

Concise summary of the `ConversationForm.vue` support ticket conversation implementation. This complements `SUPPORT_MODULE.md` and `INBOX_MODULE.md` by documenting the chat-style conversation view embedded within the inbox workflow.

---
## Overview

Goal: Provide a chat-style interface to view ticket details and conversation thread with comment posting and file attachment capabilities.

Key features implemented:
- Original ticket display (minimalist card with essential metadata: user, description, category, attachments).
- Comment thread with bubble chat layout (user comments left, staff responses right).
- Comment posting with file attachment support (single file per comment).
- Orange color scheme throughout (#f57c00 primary, #ef6c00 dark, #fdba74 borders).
- Static input section at bottom (native HTML textarea for full scroll control).
- Compact attachment UI (small icon + preview next to send button).
- Real-time date formatting (relative: "2 hours ago", "Yesterday", etc.).
- File validation (5MB max, PNG/JPG/JPEG/PDF/DOC/DOCX/TXT allowed).
- Auto-refresh after comment submission (reloads entire conversation).
- Nested within inbox module (receives ticketId from route query params).

---
## Core Endpoints

```
TICKET_CONVERSATION(id) = `support/ticket/${id}/conversation/`  // GET ticket + comments
COMMENT                 = 'support/comment/'                    // POST new comment
COMMENT_ATTACHMENT      = 'support/comment-attachment/'         // POST file for comment
```

---
## Component Location & Integration

**Path**: `src/components/forms/conversation/ConversationForm.vue`

**Parent Integration**: Embedded within the inbox module (`src/views/inbox/`). The component is rendered when a user navigates to view a specific ticket conversation.

**Route Context**: Receives `ticketId` from Vue Router query parameters (`route.query.ticketId`). This ID is passed from the inbox view when a user selects "View Conversation" or similar action.

**Data Flow**:
1. Inbox module passes ticket ID via router navigation.
2. ConversationForm watches route params and loads conversation.
3. User posts comments/attachments within conversation view.
4. Changes are persisted to backend and conversation refreshes.
5. User returns to inbox (navigation handled by parent).

---
## Main Reactive State (Highlights)

| Ref / Computed        | Purpose |
|-----------------------|---------|
| `ticketId`            | Ticket ID from route query params |
| `conversationData`    | Full conversation object (ticket + comments array) |
| `loading`             | Loading state for initial fetch |
| `error`               | Error message for fetch failures |
| `newComment`          | v-model for textarea input |
| `sendingComment`      | Loading state during comment submission |
| `commentError`        | Error message for comment post failures |
| `commentSuccess`      | Success message after comment posted |
| `selectedFile`        | Currently selected file for attachment |
| `fileError`           | File validation error message |
| `sortedComments`      | Comments sorted chronologically (oldest first) |
| `currentUserId`       | User ID from auth store (for comment authorship) |

---
## Key Methods (High Level)

| Method | Summary |
|--------|---------|
| `loadConversation()` | GET ticket conversation data (ticket + comments array); handles array or object response. |
| `sendComment()` | POST comment data (response, content, ticket, user), then upload attachment if present, reload conversation. |
| `uploadAttachment(commentId, file)` | POST FormData with file and comment ID to attach file to comment. |
| `triggerFilePicker()` | Programmatically open file input dialog. |
| `handleFileChange(e)` | Validate selected file (size, type), set `selectedFile` or show error. |
| `removeFile()` | Clear selected file and reset input. |
| `formatFileSize(bytes)` | Convert bytes to human-readable format (B, KB, MB, GB). |
| `formatDate(dateString)` | Relative date formatting ("Just now", "2 hours ago", "Yesterday", etc.). |
| `getAttachmentUrl(filePath)` | Build absolute URL for attachment file (handles relative paths). |
| `getAttachmentName(filePath)` | Extract filename from path and decode URI components. |
| `priorityColor(priority)` | Map priority level to Ionic badge color. |
| `statusColor(status)` | Map status to Ionic badge color. |

---
## Comment Posting Flow

1. **User Input**: User types message in native HTML textarea (replaces ion-textarea to prevent scroll issues).
2. **File Selection** (Optional): User clicks attachment icon, selects file via hidden input, file preview appears.
3. **Validation**: 
   - Comment must have content (trim).
   - File (if present) must be ≤5MB and allowed type.
   - User must be authenticated (currentUserId check).
4. **Submission**:
   - POST to `COMMENT` endpoint with `{response: true, content, ticket, user}`.
   - Extract comment ID from response.
   - If file selected, POST to `COMMENT_ATTACHMENT` with FormData.
5. **Refresh**: Reload entire conversation to show new comment with attachment.
6. **Feedback**: Show success message (auto-clear after 3s), clear form inputs.

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

**Original Ticket Card**:
- Minimalist display (reduced from 9+ metadata fields)
- User badge with avatar icon
- Description text (pre-wrapped)
- Category, organization, assigned-to (if present)
- Attachments list with download links

**Conversation Divider**:
- Visual separator between original ticket and comments
- Text: "─── Conversation ───"

**Comments Cascade**:
- User comments: Left-aligned, grey background (#f3f4f6)
- Staff responses: Right-aligned, orange gradient background
- Each bubble: Avatar icon, username, timestamp, content, attachments
- Empty state: "No responses yet. Start the conversation!"

**Input Section** (Static at bottom):
- Native HTML textarea (3 rows, resizable)
- Compact file preview (when file selected)
- Actions row: Attachment icon button + Send button
- Success/error messages above input

---
## Scroll Behavior Fix

**Problem**: Original `ion-textarea` caused unwanted scroll-up behavior when focused, showing white background below content.

**Solution**: Replaced with native HTML `<textarea>` element:
- Full control over focus behavior
- Custom styling matches previous appearance
- Standard CSS properties (no Ionic CSS variables)
- Focus state: orange border + box-shadow
- Eliminates Ionic's shadow DOM scroll interference

**Event Handling**:
- Keyboard shortcuts: Ctrl+Enter / Cmd+Enter to send comment
- Scroll position tracked in onMounted to prevent movement
- focusin listeners prevent scroll jumps

---
## Responsive Design

**Desktop** (>768px):
- Max width: 900px centered
- Full metadata grid visible
- Bubbles max 75% width
- Side-by-side layout for attachments

**Mobile** (≤768px):
- Reduced padding (16px)
- Bubbles max 85% width
- Stacked layout for badges/metadata
- Smaller avatar icons (1.5rem)
- Compact input section (16px padding)

---
## Integration with Auth Store

Uses Pinia `useAuthStore` for:
- `currentUserId`: Required for comment authorship
- User authentication check before comment submission
- Fallback error if user not authenticated

---
## Error Handling

**Conversation Load**:
- Loading spinner during fetch
- Error state with retry button
- Empty state if no data available

**Comment Submission**:
- Validation errors (user not authenticated, missing ticket ID)
- Network errors during POST
- Attachment upload failures (non-blocking)
- User-friendly error messages with red background

**File Validation**:
- Size exceeds 5MB: "File is too large. Max size: 5 MB"
- Unsupported type: "Unsupported file type. Allowed: PNG, JPG, JPEG, PDF, DOC, DOCX, TXT"
- Errors displayed inline with red border

---
## API Response Handling

**Conversation Data**:
- Handles both array and object responses from backend
- Extracts first element if array: `Array.isArray(data) ? data[0] : data`
- Comment array sorted chronologically (ascending)

**Comment Creation**:
- Extracts comment ID from response (handles array or object)
- Uses ID immediately for attachment upload
- Success feedback distinguishes comment-only vs comment+attachment

**Attachments**:
- Builds absolute URLs from relative paths
- Handles missing file paths gracefully
- Decodes URI-encoded filenames

---
## Minimal Usage Flow

1. User navigates from inbox to conversation view (ticketId in query params).
2. Component mounts → `loadConversation()` fetches ticket + comments.
3. Original ticket displays in orange-themed card with minimalist metadata.
4. Comment thread shows bubble chat layout (user left, staff right).
5. User types response in native textarea at bottom.
6. (Optional) User attaches file via compact icon button.
7. User clicks Send → comment POSTs, attachment uploads, conversation reloads.
8. Success message appears, form clears, new comment visible in thread.
9. User navigates back to inbox (parent handles routing).

---
## Future Enhancements (Not Implemented)

Potential features for consideration:
- Edit/delete comments (with permission checks)
- Multiple file attachments per comment
- Rich text formatting (bold, italic, links)
- Mention/tag users with @username
- Email notifications on new comments
- Draft auto-save for long responses
- Inline image preview (not just download links)
- Conversation status toggle (open/close from here)

---
## Checklist (Implemented)

- [x] Conversation fetch with ticket + comments
- [x] Original ticket display (minimalist orange card)
- [x] Comment bubble layout (user left, staff right)
- [x] Comment posting (POST with user auth)
- [x] File attachment upload (FormData POST)
- [x] Orange color scheme throughout
- [x] Native textarea (scroll issue fix)
- [x] Static input section (not fixed/sticky)
- [x] Compact attachment UI
- [x] File validation (5MB, type check)
- [x] Relative date formatting
- [x] Auto-refresh after comment
- [x] Success/error feedback
- [x] Mobile responsive design
- [x] Keyboard shortcuts (Ctrl/Cmd+Enter)

---
## Quick Reference Snippets

```js
// Load conversation
async function loadConversation() {
  const endpoint = API.TICKET_CONVERSATION(ticketId.value);
  const data = await API.get(endpoint);
  conversationData.value = Array.isArray(data) ? data[0] : data;
}

// Send comment + attachment
async function sendComment() {
  const commentData = {
    response: true,
    content: newComment.value.trim(),
    ticket: parseInt(ticketId.value),
    user: currentUserId.value
  };
  const commentResponse = await API.post(API.COMMENT, commentData);
  const commentId = Array.isArray(commentResponse) ? commentResponse[0]?.id : commentResponse?.id;
  
  if (selectedFile.value && commentId) {
    await uploadAttachment(commentId, selectedFile.value);
  }
  
  await loadConversation(); // Refresh
}

// Upload attachment
async function uploadAttachment(commentId, file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('comment', String(commentId));
  await API.post(API.COMMENT_ATTACHMENT, formData);
}
```

---
## Component Dependencies

**Vue Imports**:
- `ref`, `inject`, `onMounted`, `watch`, `computed` from Vue 3 Composition API
- `useRoute` from Vue Router
- `useAuthStore` from Pinia

**Ionic Components**:
- `IonSpinner` (loading states)
- `IonIcon` (icons throughout)
- `IonBadge` (priority/status badges)
- `IonButton` (actions)

**Utils & Composables**:
- `API` from `@/utils/api/api` (endpoints + HTTP methods)
- `icons` injected from global providers

**Native Elements**:
- `<textarea>` (replaced ion-textarea)
- `<input type="file">` (hidden, triggered programmatically)

---
## Summary

`ConversationForm.vue` delivers a clean, chat-style conversation view for support tickets, nested within the inbox workflow. Built with Vue 3 + Ionic, it focuses on simplicity, accessibility, and reliable behavior (native textarea for scroll control). The orange theme and minimalist design provide a cohesive user experience while maintaining full functionality for comment posting and file attachments.
