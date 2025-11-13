# Inbox Module (Ionic + Vue)

Concise summary of the `InboxForm.vue` support inbox implementation. This complements `SUPPORT_MODULE.md` by documenting the email‑style ticket viewer and inline management actions.

---
## Overview

Goal: Provide an email‑like UI to browse, search, read, and manage support tickets.

Key features added:
- Ticket list with search (sender, subject, body, priority) and unread toggle.
- Automatic selection + reading pane with metadata (priority, organization, machine fields).
- Assignment popover (support manager only) with delegation POST.
- Priority change popover (support manager only) with PATCH + detail sync.
- Attachments section per ticket (GET `support/attachment/?ticket_id=<id>`).
- Sender info from ticket payload: prefers `guest_name/guest_email`; otherwise uses embedded `user.full_name` and `user.email`.
- Role gating: non‑managers only see their own or assigned tickets; managers see all.
- Live refresh via notifications WebSocket (debounced on incoming events) + Live/Offline badge.
- All UI & comments standardized in English.
	- Reading pane shows Email alongside From.
	- Ticket list panel left-aligned for readability.

---
## Core Endpoints

```
SUPPORT_TICKET        = 'support/ticket/'          // List + detail + priority PATCH
SUPPORT_MEMBERS       = 'support/ticket/get_support_members/'
DELEGATE(ticketId)    = `support/ticket/${id}/delegate/`
ATTACMEENT_CREATE     = 'support/attachment/'      // ?ticket_id=<id>
```

---
## Main Reactive State (Highlights)

| Ref / Computed        | Purpose |
|-----------------------|---------|
| `messages`            | Mapped ticket list (unread flag locally) |
| `filteredMessages`    | Search + unread + role-based filter |
| `selectedId` / `selectedMessage` | Current ticket in reading pane |
| `assigneeId`          | Current selected assignee (popover) |
| `attachments`         | Mapped list of file attachments |
| `isSupportManager`    | Permission gate for actions & visibility |
| `notifications`       | Latest WebSocket notifications (debounced refresh) |

---
## Key Methods (High Level)

| Method | Summary |
|--------|---------|
| `mapTicketToMessage(t)` | Normalize backend ticket into inbox message shape. |
| `fetchTickets()`        | GET tickets, map (including embedded user/guest info), sort, select first, init assignee & attachments. |
| `fetchSupportMembers()` | Load support staff (with role) for assignment popover. |
| `ensureMembers()`       | Lazy fetch members before opening assignment popover. |
| `selectMessage(id)`     | Set current ticket, mark read, load attachments. |
| `setTicketPriority(level)` | PATCH priority then attempt detail GET for sync; guarded by manager role. |
| `fetchAttachments(ticketId)` | GET attachments via query param; filter by ticket; map to link model. |
| Assignee watcher        | POST delegate when `assigneeId` changes (guarded). |

---
## Role Gating Logic

`isSupportManager` is true when:
- User is superuser or admin (from auth store), OR
- User appears in support members list with a role string containing “manager”.

Non‑managers: list limited to tickets they created (`user_id`) or are assigned to (`assigned_to`). Assignment / priority controls hidden.

---
## Live Updates

Uses existing notifications WebSocket composable: watches the most recent notification object and debounces (≈700ms) a `fetchTickets()` refresh. Connection status badge shows “Live” (connected) or “Offline”. This avoids manual polling while remaining lightweight.

Fallback strategy (optional): could add timed polling if no notifications arrive for an extended interval; not necessary in current implementation.

---
## Attachments Handling

`fetchAttachments(ticketId)` queries `support/attachment/?ticket_id=<id>` then filters results by `ticket_id` (or nested `ticket.id`). Empty results surface a friendly message: “No attachments found here”. 404 noise is suppressed.

Mapping logic extracts a stable name from file path or filename fields and builds absolute URLs (relative paths converted using API base URL).

---
## User Info Mapping

Sender information comes bundled with each ticket. Mapping precedence:
1) If the ticket has `guest_name`/`guest_email`, those are used.
2) Otherwise, use the embedded `user.full_name` and `user.email` from `ticket.user`.

No external user lookup is performed anymore.

---
## Priority & Assignment

Both actions are guarded by `isSupportManager`. Priority updates PATCH the ticket then attempt a detail GET for server‑authoritative values. Assignment is persisted via the delegate POST watcher; failures revert local state and show an error message.

---
## Filtering Summary

`filteredMessages` applies in order:
1. Role scope (manager vs. own/assigned). 
2. Unread toggle. 
3. Search term across from/subject/snippet/body/priority (case‑insensitive). 
4. Sort by descending date.

---
## Small UX Details

- Inline unread toggle (total unread badge removed).
- Priority badge color mapping (danger/high|urgent, warning/medium, medium/low).
- Live/Offline connection badge co‑located with search actions.
- Popovers close automatically after action selection.
- Success/error feedback auto‑clears (≈1.8s) for assignment / priority.
 - Ticket list panel left‑aligned for better visual scan.
 - Reading pane shows Email when available.

---
## Minimal Usage Flow

1. Component mounts → members then tickets fetched.
2. First ticket auto‑selected; attachments + user names preloaded.
3. User searches or toggles unread; list reacts instantly.
4. Manager may open assignment or priority popovers; changes persist and reflect.
5. Incoming notifications trigger silent refresh.

---
## Extensibility Notes (Future)

Potential enhancements (not implemented yet):
- Add fallback polling if WebSocket disconnected for > N minutes.
- Inline reply or comment thread panel.
- Bulk actions (mark read, change priority) for selected group.
- Column for status or SLA age indicator.

---
## Checklist (Implemented)

- [x] Ticket fetch + mapping
- [x] Search + unread filter
- [x] Role gating (manager vs. others)
- [x] Assignment popover (POST delegate)
- [x] Priority update (PATCH + sync)
- [x] Sender info from embedded ticket.user (guest fields preferred)
- [x] Attachments by ticket id
- [x] WebSocket live refresh (debounced)
- [x] English-only comments & UI strings

---
## Quick Reference Snippets

```js
// Fetch + map
async function fetchTickets() { /* GET, map, select, prefetch names, attachments */ }

// Priority
async function setTicketPriority(level) { /* PATCH + detail GET, guarded */ }

// Assignment watcher
watch(assigneeId, async (newId, oldId) => { /* POST delegate, guarded */ });

// Attachments
async function fetchAttachments(ticketId) { /* GET ?ticket_id=, map, friendly empty */ }
```

---
## Summary

`InboxForm.vue` delivers a lean, role‑aware, real‑time support inbox built on existing API endpoints and the notification WebSocket, focusing on clarity, low coupling, and incremental enhancement potential.

